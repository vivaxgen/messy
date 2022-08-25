
from messy.views import roles, render_to_response, get_dbhandler
from messy.lib import roles as r

from rhombus.lib import tags_b46 as t
from rhombus.views.home import login as rb_login, logout as rb_logout
from rhombus.views import fso
from pyramid.response import FileResponse

import docutils.core
import os


@roles(r.PUBLIC)
def index(request):

    dbh = get_dbhandler()
    dbsession = dbh.session()

    html = t.div()[
        t.h2('Data Status'),
        t.div(class_='row')[
            t.div('Total collection:', class_='col-3 offset-1'),
            t.div(str(dbh.Collection.query(dbsession).count()), class_='col'),
        ],
        t.div(class_='row')[
            t.div('Total samples:', class_='col-3 offset-1'),
            t.div(str(dbh.Sample.query(dbsession).count()), class_='col'),
        ],
        #t.div(class_='row')[
        #    t.div('Total sequences:', class_='col-3 offset-1'),
        #    t.div(str(dbh.Sequence.query(dbsession).count()), class_='col'),
        #]
    ]

    return render_to_response(
        'messy:templates/generic_page.mako',
        {
            'html': html,
        }, request=request
    )


def login(request):
    return rb_login(request)


def logout(request):
    return rb_logout(request)


@roles(r.PUBLIC)
def docs(request):

    path = os.path.normpath(request.matchdict.get('path', '') or '/index.rst')
    path = '/' + path if not path.startswith('/') else path
    return fso.serve_file(path, mount_point=('/', "messy:../docs/help"),
                          formatter=lambda abspath: formatter(abspath, request))


def formatter(abspath, request):

    basepath, ext = os.path.splitext(abspath)

    if ext == '.rst':
        # restructuredtext
        with open(abspath) as f:
            text = f.read()
            content = t.literal(render_rst(text))

        return render_to_response(
            'messy:templates/generic_page.mako',
            {
                'html': content,
            }, request=request)

    elif ext == '.md':
        raise NotImplementedError

    else:
        return FileResponse(abspath)


def render_rst(text, format='html'):

    parts = docutils.core.publish_parts(text, writer_name=format,
                                        settings_overrides={'initial_header_level': 2})
    if format == 'html':
        return parts['html_body']
    return None

# EOF
