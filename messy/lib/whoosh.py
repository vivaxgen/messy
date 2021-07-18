
# this class provide whoosh interface

from whoosh.fields import SchemaClass, TEXT, ID, NUMERIC, STORED, KEYWORD
from whoosh.index import create_in, open_dir, exists_in
from whoosh.qparser import QueryParser
from whoosh.query import Term, FuzzyTerm

from rhombus.models.meta import RhoSession
from rhombus.lib.utils import get_dbhandler, cerr, cexit
from sqlalchemy import event

import os


class SearchScheme(SchemaClass):

    dbid = NUMERIC(stored=True, unique=True)
    mtime = STORED
    text = TEXT


class Searchable(object):

    __slots__ = ['dbid', 'mtime', 'text']

    def __init__(self, dbid, mtime, text):
        self.dbid = dbid
        self.mtime = mtime
        self.text = text


class ClassIndexer(object):

    def __init__(self, ix, fields):
        self.ix = ix
        self.fields = fields

    def text(self, obj):
        return ' '.join(getattr(obj, f) for f in self.fields)


class Updater(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.created_objects = {}
        self.updated_objects = {}
        self.deleted_objects = {}


class IndexService(object):

    def __init__(self, basepath):
        self.basepath = basepath
        self.cis = {}

        event.listen(RhoSession, "after_flush", self.after_flush)
        event.listen(RhoSession, "after_commit", self.after_commit)
        event.listen(RhoSession, "after_rollback", self.after_rollback)

        # register classes
        from messy.models import dbschema
        self.register_class(dbschema.EK, 'key', 'desc')
        self.register_class(dbschema.Institution)

    def register_class(self, class_, *fields):

        if class_ in self.cis:
            raise RuntimeError(f'Class f{class_} is already registered in whoosh!')

        path = os.path.join(self.basepath, class_.__name__)

        if exists_in(path):
            ix = open_dir(path)
        else:
            if not os.path.exists(path):
                os.makedirs(path)
            ix = create_in(path, SearchScheme)

        search_fields = list(getattr(class_, '__searchable__', []))
        if len(fields) > 0:
            search_fields = search_fields + list(fields)

        self.cis[class_] = ClassIndexer(ix, search_fields)
        class_.search_text = TextSearcher(class_, self.cis[class_])

    def after_flush(self, session, context):

        updater = self.get_updater(session)

        for n in session.new:
            ci = self.cis.get(n.__class__, None)
            if ci:
                s = Searchable(n.id, n.stamp, ci.text(n))
                try:
                    updater.created_objects[n.__class__][n.id] = s
                except KeyError:
                    updater.created_objects[n.__class__] = {n.id: s}

        for n in session.dirty:
            ci = self.cis.get(n.__class__, None)
            if ci:
                s = Searchable(n.id, n.stamp, ci.text(n))
                try:
                    updater.updated_objects[n.__class__][n.id] = s
                except KeyError:
                    updater.updated_objects[n.__class__] = {n.id: s}

        for n in session.deleted:
            ci = self.cis.get(n.__class__, None)
            if ci:
                try:
                    updater.deleted_objects[n.__class__][n.id] = None
                except KeyError:
                    updater.deleted_objects[n.__class__] = {n.id: None}

    def after_commit(self, session):

        updater = self.get_updater(session)

        for class_ in updater.deleted_objects:
            with self.cis[class_].ix.writer() as writer:
                for dbid in updater.deleted_objects[class_]:
                    writer.delete_by_term('dbid', dbid)

        for class_ in updater.deleted_objects:
            with self.cis[class_].ix.writer() as writer:
                for obj in updater.created_objects[class_].values():
                    writer.add_document(dbid=obj.dbid, mtime=obj.mtime, text=obj.text)

        for class_ in updater.updated_objects:
            with self.cis[class_].ix.writer() as writer:
                for obj in updater.updated_objects[class_].values():
                    writer.delete_by_term('dbid', obj.dbid)
                    writer.add_document(dbid=obj.dbid, mtime=obj.mtime, text=obj.text)

        updater.reset()

    def after_rollback(self, session):

        updater = self.get_updater(session)
        updater.reset()

    def get_updater(self, session):

        if hasattr(session, 'ix_updater'):
            return getattr(session, 'ix_updater')

        updater = Updater()
        setattr(session, 'ix_updater', updater)
        cerr('initialize Whoosh updater')
        return updater


_INDEX_SERVICE_ = None


def set_index_service(index_service):
    global _INDEX_SERVICE_
    _INDEX_SERVICE_ = index_service


def get_index_service():
    global _INDEX_SERVICE_
    if _INDEX_SERVICE_ is None:
        raise RuntimeError('FATAL ERR: call set_index_service() first!')
    return _INDEX_SERVICE_


# utilities

def reindex():

    dbh = get_dbhandler()
    index_service = get_index_service()

    for class_ in index_service.cis:
        ci = index_service.cis[class_]
        with ci.ix.writer() as writer:

            for obj in class_.query(dbh.session()):
                writer.delete_by_term('dbid', obj.id)
                writer.add_document(dbid=obj.id, mtime=obj.stamp, text=ci.text(obj))
                cerr(f'reindex {class_.__name__}: {obj.id}')


class CustomFuzzyTerm(FuzzyTerm):
    """
    Custom FuzzyTerm query parser to set a custom maxdist
    """

    def __init__(self, fieldname, text, boost=1.0, maxdist=2, prefixlength=1):
        FuzzyTerm.__init__(self, fieldname, text, boost, maxdist, prefixlength)


class TextSearcher(object):

    def __init__(self, class_, ci):
        self.class_ = class_
        self.ci = ci
        self.query_parser = QueryParser('text', schema=ci.ix.schema, termclass=CustomFuzzyTerm)

    def __call__(self, text, session, limit=None, id_only=False):

        text = ' OR '.join(text.replace(' or ', ' ').replace(' and ', ' ').split())
        query = self.query_parser.parse(text)
        with self.ci.ix.searcher() as searcher:
            results = searcher.search(query, limit=limit)
            dbids = [r['dbid'] for r in results]
        if id_only:
            return dbids
        return [self.class_.query(session).get(dbid) for dbid in dbids]

# EOF
