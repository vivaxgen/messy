
from rhombus.lib.utils import get_dbhandler
from rhombus.lib import tags as t
from rhombus.views import generate_sesskey
from messy.views import BaseViewer, Response, m_roles
from messy.ext.ngsmgr.lib import roles as r

# global, singleton variables

# the following dictionary holds active file upload session keys in memory
# since file upload session should be short-lived, unlike the batched
# uploadjob
__active_upload_sesskey__ = {}



class FastqPairViewer(BaseViewer):

    template_edit = 'messy:templates/fileupload_page.mako'

    managing_roles = BaseViewer.managing_roles + [r.NGSRUN_MANAGE]
    modifying_roles = managing_roles + [r.NGSRUN_MODIFY]

    object_class = get_dbhandler().FastqPair
    fetch_func = get_dbhandler().get_ngsruns_by_ids
    edit_route = 'messy-ngsmgr.fastqpair-edit'
    view_route = 'messy-ngsmgr.fastqpair-view'
    attachment_route = None

    form_fields = {
        'sample_id': ('messy-ngsmgr-fastqpair-sample_id', ),
        'panel_id': ('messy-ngsmgr-fastqpair-panel_id', ),
        'ngsrun_id': ('messy-ngsmgr-fastqpair-ngsrun_id', ),
    }

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.obj
        dbh = self.dbh
        rq = self.request
        ff = self.ffn

        sesskey = generate_sesskey(rq.user.id)

        eform = t.form(name='messy-run', method=t.POST, enctype=t.FORM_MULTIPART, readonly=readonly,
                       update_dict=update_dict).add(
            self.hidden_fields(obj),
            t.input_select(ff('sample_id') + '-' + sesskey,
                           'Sample', value=obj.sample_id,
                           options=[(obj.sample_id, obj.sample.fullcode)] if obj.sample_id else [],
                           offset=2, size=2),
            t.input_select(ff('panel_id') + '-' + sesskey,
                           'Panel', value=obj.panel_id,
                           options=[(obj.panel_id, obj.panel.code)] if obj.panel_id else [],
                           offset=2, size=2),
            t.input_select(ff('ngsrun_id') + '-' + sesskey,
                           'NGS Run', value=obj.ngsrun_id or -1,
                           options=[(obj.ngsrun_id, obj.ngsrun.code)] if obj.ngsrun else [],
                           offset=2, size=2),
        )

        fileinput_tag = f'fileinput-{sesskey}'
        eform.add(
            t.div(id=fileinput_tag + '-1', name=fileinput_tag + '-1'),
            t.div(id=fileinput_tag + '-2', name=fileinput_tag + '-2'),
        )

        jscode = '''
    $('#{fileinput_tag}-1').filepond({{
        server: {{
          url: '{target1_url}',
        }},
        allowDrop: true,
        allowMultiple: false,
        ChunkUploads: true,
        chunkForce: true,
        chunkSize: 262144, // 256KB = 256 * 1024 bytes
    }});
    $('#{fileinput_tag}-2').filepond({{
        server: {{
          url: '{target2_url}',
        }},
        allowDrop: true,
        allowMultiple: false,
        ChunkUploads: true,
        chunkForce: true,
        chunkSize: 262144, // 256KB = 256 * 1024 bytes
    }});
        '''.format(fileinput_tag=fileinput_tag,
                   target1_url=rq.route_url('messy-ngsmgr.fastqpair-target1',
                                            sesskey=sesskey),
                   target2_url=rq.route_url('messy-ngsmgr.fastqpair-target2',
                                            sesskey=sesskey),
                   )

        return eform, jscode

    def action_upload(self):

        _method = self.request.POST.get('_method')

        if _method == 'new':

            return Response(
            )

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
                        href=request.route_url('messy-ngsmgr.panel-view', id=fastqpair.panel_id)
                    )
                ) if 'panel' in additional_fields else '',
                t.td(
                    t.a(
                        f'{fastqpair.ngsrun.code}',
                        href=request.route_url('messy-ngsmgr.ngsrun-view', id=fastqpair.ngsrun_id)
                    )
                ) if 'ngsrun' in additional_fields else '',
                t.td('uploaded/mapped/var-called'),
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
