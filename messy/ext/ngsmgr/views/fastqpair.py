
from rhombus.lib.utils import get_dbhandler
from rhombus.lib.fileutils import get_file_size
from rhombus.lib import tags as t
from rhombus.views import generate_sesskey
from messy.views import (BaseViewer, Response, m_roles, select2_lookup, render_to_response,
                         modal_error, modal_delete, HTTPFound)
from messy.ext.ngsmgr.lib import roles as r

from urllib.parse import unquote

import time


class FastqPairViewer(BaseViewer):

    template_edit = 'messy:templates/fileupload_page.mako'

    managing_roles = BaseViewer.managing_roles + [r.NGSRUN_MANAGE, r.SAMPLE_MANAGE]
    modifying_roles = managing_roles + [r.NGSRUN_MODIFY, r.SAMPLE_MODIFY]

    object_class = get_dbhandler().FastqPair
    fetch_func = get_dbhandler().get_ngsruns_by_ids
    edit_route = 'messy-ngsmgr.fastqpair-edit'
    view_route = 'messy-ngsmgr.fastqpair-view'
    attachment_route = None

    form_fields = {
        'sesskey': ('messy-ngsmgr-fastqpair-sesskey', ),
        'sample_id!': ('messy-ngsmgr-fastqpair-sample_id', ),
        'panel_id!': ('messy-ngsmgr-fastqpair-panel_id', ),
        'ngsrun_id!': ('messy-ngsmgr-fastqpair-ngsrun_id', ),
    }

    def can_modify_XXX(self, obj):
        obj = obj or self.obj
        user = self.request.user

        # if user can modify the sample, the user can modify this fastqfile as well
        if obj.sample.can_modify(user):
            return True

        return False

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.obj
        dbh = self.dbh
        rq = self.request
        ff = self.ffn

        sesskey = generate_sesskey(rq.user.id)
        fileinput_tag = 'fastqread'

        eform = t.form(name='messy-run', method=t.POST, enctype=t.FORM_MULTIPART,
                       readonly=readonly, update_dict=update_dict).add(
            self.hidden_fields(obj),
            t.input_hidden(ff('sesskey'), value=sesskey),
            t.inline_inputs(
                t.input_select(
                    ff('sample_id!') + '-' + sesskey,
                    'Sample', value=obj.sample_id,
                    options=[(obj.sample_id, obj.sample.fullcode)] if obj.sample_id else [],
                    offset=1, size=3, required=True),
                t.input_select(
                    ff('panel_id!') + '-' + sesskey,
                    'Panel', value=obj.panel_id,
                    options=[(obj.panel_id, obj.panel.code)] if obj.panel_id else [],
                    offset=1, size=3, required=True),
                t.input_select(
                    ff('ngsrun_id!') + '-' + sesskey,
                    'NGS Run', value=obj.ngsrun_id or -1,
                    options=[(obj.ngsrun_id, obj.ngsrun.code)] if obj.ngsrun else [],
                    offset=1, size=3, required=True),
                name='messy-ngsmgr-fastqpair-fieldset'
            ),
            t.div(id=fileinput_tag + '-1', name=fileinput_tag + '-1'),
            t.div(id=fileinput_tag + '-2', name=fileinput_tag + '-2'),
            t.custom_submit_bar(('Save', 'add')).set_offset(2),
        )

        jscode = ''
        jscode += select2_lookup(tag=self.ffn('ngsrun_id!') + '-' + sesskey, minlen=3,
                                 placeholder="Type an NGS Run code",
                                 parenttag="messy-ngsmgr-fastqpair-fieldset",
                                 usetag=False,
                                 url=unquote(self.request.route_url('messy-ngsmgr.ngsrun-lookup'))
                                 )

        jscode += select2_lookup(tag=self.ffn('sample_id!') + '-' + sesskey, minlen=3,
                                 placeholder="Type a sample code",
                                 parenttag="messy-ngsmgr-fastqpair-fieldset",
                                 usetag=False,
                                 url=unquote(self.request.route_url('messy.sample-lookup'))
                                 )

        jscode += select2_lookup(tag=self.ffn('panel_id!') + '-' + sesskey, minlen=3,
                                 placeholder="Type a panel code",
                                 parenttag="messy-ngsmgr-fastqpair-fieldset",
                                 usetag=False,
                                 url=unquote(self.request.route_url('messy-ngsmgr.panel-lookup'))
                                 )

        jscode += '''

    $('#{fileinput_tag}-1').filepond({{
        server: {{
          url: '{target_url}',
          fetch: null,
          revert: null,
        }},
        allowDrop: true,
        allowMultiple: false,
        labelIdle: "Drag & Drop or browse for 1st read (mandatory)",
        stylePanelLayout: 'compact',
        ChunkUploads: true,
        chunkForce: true,
        chunkSize: 1048576, // 1MB = 1024 * 1024 bytes
    }});
    $('#{fileinput_tag}-2').filepond({{
        server: {{
          url: '{target_url}',
          fetch: null,
          revert: null,
        }},
        allowDrop: true,
        allowMultiple: false,
        labelIdle: "Drag & Drop or browse for 2nd read (if available)",
        ChunkUploads: true,
        chunkForce: true,
        chunkSize: 1048576, // 1MB = 1024 * 1024 bytes
    }});
        '''.format(fileinput_tag=fileinput_tag,
                   target_url=unquote(rq.route_url('messy-ngsmgr.fastqpair-target',
                                                   sesskey=sesskey)),
                   )

        return eform, jscode

    def add_helper(self):

        rq = self.request
        user = rq.user
        dbh = self.dbh
        ff = self.ffn

        if rq.method == 'POST':

            # get all fastqpair session keys
            keys = rq.POST.getall(ff('sesskey'))
            if not any(keys):
                raise RuntimeError('sesskey is not provided with the request form')

            for k in keys:
                # iterate all of individual fastqpair

                sample_id = int(rq.POST.get(ff('sample_id!') + '-' + k))
                panel_id = int(rq.POST.get(ff('panel_id!') + '-' + k))
                ngsrun_id = int(rq.POST.get(ff('ngsrun_id!') + '-' + k))

                fastquploadjobs = dbh.get_uploadjobs_by_sesskeys([k],
                                                                 groups=user.groups,
                                                                 user=user)
                if not(any(fastquploadjobs)):
                    raise RuntimeError('the user has not selecting any file')

                fastquploadjob = fastquploadjobs[0]
                file_count = 0
                for uploaditem in fastquploadjob.uploaditems:
                    file_count += 1
                    uploaditem.json = dict(sample_id=sample_id,
                                           panel_id=panel_id,
                                           readno=uploaditem.json['readno']
                                           )
                fastquploadjob.json = dict(ngsrun_id=ngsrun_id, file_count=file_count)
                fastquploadjob.commit(user=user)

                # once commit, we remove the job
                dbh.session().delete(fastquploadjob)

            return render_to_response('messy:templates/generic_page.mako', {
                "html": 'The fastq files have been saved to system',
            }, request=rq)


        return super().add_helper()

    @m_roles(r.PUBLIC)
    def target(self):

        rq = self.request
        dbh = self.dbh
        user = rq.user
        sesskey = rq.matchdict.get('sesskey')

        # sanity check,

        # start of upload, hence prepare a new uploadjob or create a new one
        if rq.POST.get('fastqread-1'):
            dbh.FastqUploadJob.get_or_create(sesskey, rq.user, dbh)
            return Response("1")
        elif rq.POST.get('fastqread-2'):
            dbh.FastqUploadJob.get_or_create(sesskey, rq.user, dbh)
            return Response("2")

        # pass this, we will have the first and consecutive chunks from the browser

        job = dbh.get_uploadjobs_by_sesskeys([sesskey], groups=user.groups, user=rq.user)[0]

        if (rq.method == 'PATCH'
            and (key := rq.params.get('patch'))
                and 'Upload-Name' in rq.headers):

            # get file information
            offset = int(rq.headers['Upload-Offset'])
            filename = rq.headers['Upload-Name']
            size = int(rq.headers['Upload-Length'])

            # create or get uploaditem
            if offset == 0:
                # for new file, we create a new uploaditem and put the necessary info
                uploaditem = dbh.UploadItem(uploadjob=job,
                                            filename=filename,
                                            total_size=size,
                                            json={'readno': int(key)}
                                            )
                dbh.session().add(uploaditem)
                mode = 'wb'

            else:
                try:
                    uploaditem = job.filenames[filename]
                except KeyError:
                    return Response(json=dict(message="File has not been prepared"),
                                    status="403",
                                    content_type="text/plain",
                                    headers=[('Error-Message',
                                             'ERR - File has not been prepared')])
                mode = 'r+b'

            path = uploaditem.get_fullpath()

            with open(path, mode) as fout:

                # check continuity of the transfer
                prev_size = get_file_size(fout)
                if offset != prev_size:
                    return Response(json=dict(message="File offset is not correct"),
                                    status="400",
                                    content_type="text/plain",
                                    headers=[('Error-Message',
                                              'ERR - File offset is not correct')])

                # move file pointer to the end of file and append the content from body
                fout.seek(0, 2)
                fout.write(rq.body)
                curr_size = get_file_size(fout)

            if curr_size == uploaditem.total_size:
                uploaditem.completed = 1

            return Response('ok')

        if rq.method == 'DELETE':
            # ignore this
            return Response()

        return Response(json=dict(message="Protocol not implemented"),
                        status="400",
                        content_type="text/plain",
                        headers=[('Error-Message',
                                  'ERR - Protocol not implemented')])

    def action_post(self):

        rq = self.request
        dbh = self.dbh

        match _method := rq.POST.get('_method'):

            case 'delete':

                fastqpair_ids = [int(x) for x in rq.POST.getall('fastqpair-ids')]
                fastqpairs = dbh.get_fastqpairs_by_ids(fastqpair_ids,
                                                       groups=None,
                                                       user=rq.user)

                if not any(fastqpairs):
                    return Response(
                        modal_error(
                            content="Please select fastq to be removed!")
                    )

                return Response(
                    modal_delete(
                        title='Removing fastq file(s)',
                        content=t.literal(
                            'You are going to remove the following fastq file(s): '
                            '<ul>'
                            + ''.join(f'<li>paired fastq files with id: {fq.id}</li>'
                                      for fq in fastqpairs)
                            + '</ul>'
                        ), request=rq,
                    ), request=rq
                )

            case 'delete/confirm':

                fastqpair_ids = [int(x) for x in rq.POST.getall('fastqpair-ids')]
                fastqpairs = dbh.get_fastqpairs_by_ids(fastqpair_ids,
                                                       groups=None,
                                                       user=rq.user)

                sess = dbh.session()
                count = left = 0
                for fq in fastqpairs:
                    if fq.can_modify(rq.user):
                        fq.clear()
                        sess.delete(fq)
                        count += 1
                    else:
                        left += 1

                sess.flush()

                rq.session.flash(
                    ('success', f'You have successfully removed {count} paired fastq file(s), '
                                f'kept {left} paired fastq file(s).')
                )

                return HTTPFound(location=rq.referer)

        raise ValueError(f'unknown method: {_method}')

    @m_roles(r.PUBLIC)
    def uploadmgr(self):

        session_table, session_code = generate_uploadsession_table(self)

        raise

    @m_roles(r.PUBLIC)
    def upload(self):
        """ manage upload based on session key
        """


def generate_fastqpair_table(fastqpairs, request, can_modify=False,
                             additional_fields=None):

    if additional_fields is None:
        additional_fields = ['sample', 'ngsrun', 'panel']

    table_body = t.tbody()

    for fastqpair in fastqpairs:
        try:
            table_body.add(
                t.tr(
                    t.td(t.literal(
                        f'<input type="checkbox" name="fastqpair-ids" value="{fastqpair.id}" />')),
                    t.td(fastqpair.filename1, t.br, (fastqpair.filename2 or '')),
                    t.td(
                        t.a(
                            f'{fastqpair.sample.code}/{fastqpair.sample.collection.code}',
                            href=request.route_url('messy.sample-view', id=fastqpair.sample_id)
                        )
                    ) if 'sample' in additional_fields else '',
                    t.td(
                        t.a(
                            f'{fastqpair.panel.code}',
                            href=request.route_url('messy-ngsmgr.panel-view',
                                                   id=fastqpair.panel_id)
                        )
                    ) if 'panel' in additional_fields else '',
                    t.td(
                        t.a(
                            f'{fastqpair.ngsrun.code}',
                            href=request.route_url('messy-ngsmgr.ngsrun-view',
                                                   id=fastqpair.ngsrun_id)
                        )
                    ) if 'ngsrun' in additional_fields else '',
                    t.td('uploaded/mapped/var-called'),
                )
            )

        except:
            table_body.add(
                t.tr(
                    t.td(t.literal(
                        f'<input type="checkbox" name="fastqpair-ids" value="{fastqpair.id}" />')),
                    t.td(f'Error fastqpair id: {fastqpair.id}')
                )
            )

    fastqpair_table = t.table(class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('FastQ Filename'),
                t.th('Sample') if 'sample' in additional_fields else '',
                t.th('Panel') if 'panel' in additional_fields else '',
                t.th('NGS Run') if 'ngsrun' in additional_fields else '',
                t.th('Status'),
            )
        )
    ]

    fastqpair_table += table_body
    jscode = ''

    if can_modify:

        # prepare selection bar
        bar = t.selection_bar(
            'fastqpair-ids', action=request.route_url('messy-ngsmgr.fastqpair-action')
        )
        fastqpair_table, code = bar.render(fastqpair_table)
        jscode += code

    return fastqpair_table, jscode


js_fileupload = '''
        'use strict';

        $('#upload-1').fileupload({
            dataType: 'json',
            formData: {read: 1},
            maxChunkSize: 1000000,
            done: function (e, data) {
                $('#cmsfix-slug').val( data.result.basename );
                $('#cmsfix-basename').text( data.result.basename );
                $('#cmsfix-size').text( data.result.size );
                $('#cmsfix-filename').val( data.result.basename )
                $('#cmsfix-mimetype_id').val( data.result.mimetype_id );
            },
            progressall: function (e, data) {
                var progress = parseInt(data.loaded / data.total * 100, 10);
                $('#fileprogress-1 .progress-bar').css('width', progress + '%%');
            },
            start: function (e) {
                $('#fileprogress-1 .progress-bar').css('width','0%%');
                $('#fileprogress-1').show();
            },
            stop: function(e) {
                $('#fileprogress-1').hide();
            }
        }).prop('disabled', !$.support.fileInput)
            .parent().addClass($.support.fileInput ? undefined : 'disabled');

'''
# EOF
