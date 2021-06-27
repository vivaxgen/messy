
from messy.views import *
import dateutil


class SequenceViewer(BaseViewer):
    """
        Design outline
        --------------

        SequenceViewer performs sequence data visualization and limited editing,
        as most of the data in Sequence object should be uploaded with output of
        analysis software and/or data processing pipelines.

    """


    managing_roles = BaseViewer.managing_roles + [ SEQUENCE_MANAGE ]
    modifying_roles = managing_roles + [ SEQUENCE_MODIFY ]

    object_class = get_dbhandler().Sequence
    fetch_func = get_dbhandler().get_sequences_by_ids
    edit_route = 'messy.sequence-edit'
    view_route = 'messy.sequence-view'

    form_fields = {
        'sequencingrun_id': ('messy-sequence-sequencingrun_id', ),
        'sample_id': ('messy-sequence-sample_id', ),
        'method_id': ('messy-sequence-method_id', ),
        'accid': ('messy-sequence-accid', ),
        'submission_date?': ('messy-sequence-submission_date', dateutil.parser.parse),
        'lineage_1': ('messy-sequence-lineage_1', ),
        'prob_1': ('messy-sequence-prob_1', float),
        'lineage_2': ('messy-sequence-lineage_2', ),
        'prob_2': ('messy-sequence-prob_2', float),
        'lineage_3': ('messy-sequence-lineage_2', ),
        'prob_3': ('messy-sequence-prob_2', float),
        'avg_depth': ('messy-sequence-avg_depth'),
        'length': ('messy-sequence-length', ),
        'gaps': ('messy-sequence-gaps', ),
        'depth_plot?': ('messy-sequence-depth_plot', lambda x: x.file.read() if x != b'' else None),
        'sequence': ('messy-sequence-sequence', ),
    }

    @m_roles(PUBLIC)
    def index(self):

        sequences = self.dbh.get_sequences(groups=None, fetch=False)
        html, code = generate_sequence_table(sequences, self.request)
        html = div()[ h2('Sequences'), html ]

        return render_to_response("messy:templates/generic_page.mako",
            { 'html': html
            },
            request = self.request)

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.obj
        dbh = self.dbh
        ff = self.form_fields

        # dealing with all input_select values
        sequencingrun = obj.sequencingrun
        sample = obj.sample

        eform = form(name='messy-sample', method=POST, enctype=FORM_MULTIPART)[
            self.hidden_fields(obj),
            fieldset(
                input_select(ff['sequencingrun_id'][0], 'Sequencing Run', value=obj.sequencingrun_id,
                             offset=2, size=3, static=readonly,
                             options=[(sequencingrun.id, sequencingrun.code)] if sequencingrun else []),
                input_select(ff['sample_id'][0], 'Sample', value=obj.sample_id,
                             offset=2, size=4, static=readonly,
                             options=[(sample.id, f'{sample.code} | {sample.collection.code}')] if sample else []),
                input_text(ff['accid'][0], 'Acc ID', value=obj.accid,
                           offset=2, static=readonly, update_dict=update_dict),
                input_text(ff['submission_date?'][0], 'Submission Date', value=obj.submission_date,
                           offset=2, static=readonly, update_dict=update_dict),
            ),
            fieldset(
                form_submit_bar(create) if not readonly else div(),
                name='footer'
            ),
        ]

        return div()[h2('Sequence'), eform], ''


def generate_sequence_table(sequences, request):

    table_body = tbody()

    not_guest = not request.user.has_roles( GUEST )

    for sequence in sequences:
        sample = sequence.sample
        table_body.add(
            tr(
                td(literal('<input type="checkbox" name="sequence-ids" value="%d" />' % sequence.id)
                    if not_guest else ''),
                td( a(sample.code, href=request.route_url('messy.sequence-view', id=sequence.id)) ),
                td( sequence.accid),
                td( sample.sequence_name ),
                td( sample.location),
                td( sample.collection_date),
                td( sample.lineage_1),
            )
        )

    sequence_table = table(class_='table table-condensed table-striped')[
        thead(
            tr(
                th('', style="width: 2em"),
                th('Code'),
                th('Acc ID'),
                th('Name'),
                th('Location'),
                th('Collection Date'),
                th('Lineage 1'),
            )
        )
    ]

    sequence_table.add( table_body )

    if not_guest:
        add_button = ( 'New sequence',
                        request.route_url('messy.sequence-add')
        )

        bar = selection_bar('sequence-ids', action=request.route_url('messy.sequence-action'),
                    add = add_button)
        html, code = bar.render(sequence_table)

    else:
        html = div(sample_table)
        code = ''

    return html, code
