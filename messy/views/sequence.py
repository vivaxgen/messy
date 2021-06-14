
from messy.views import *

class SequenceViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [ SEQUENCE_MANAGE ]
    modifying_roles = managing_roles + [ SEQUENCE_MODIFY ]

    object_class = get_dbhandler().Sequence
    fetch_func = get_dbhandler().get_sequences_by_ids
    edit_route = 'messy.sequence-edit'
    view_route = 'messy.sequence-view'


    @m_roles(PUBLIC)
    def index(self):

        sequences = self.dbh.get_sequences(groups=None, fetch=False)
        html, code = generate_sequence_table(sequences, self.request)
        html = div()[ h2('Sequences'), html ]

        return render_to_response("messy:templates/generic_page.mako",
            { 'html': html
            },
            request = self.request)


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
