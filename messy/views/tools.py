
from messy.views import render_to_response, get_dbhandler
import rhombus.lib.tags_b46 as t


class ToolsViewer(object):

    def __init__(self, request):
        self.request = request
        self.dbh = get_dbhandler()

    def index(self):

        html = t.div(t.h2('Tools'))
        html += t.p('Under construction.')

        readonly = False
        eform = t.form(name='a_form', method=t.POST, readonly=readonly)[
            t.fieldset(
                t.input_hidden('field_hidden_1', value='Ok'),
            ),
            t.fieldset(
                t.input_text('field_1', 'Field 1', value=None, offset=2, size=3),
                t.input_text('field_2', 'Field 22', value=None, offset=2, size=3),
            ),
            t.fieldset(
                t.inline_inputs(
                    t.input_text('field_in_1', 'Inline 1', value=None, offset=2, size=2),
                    t.input_text('field_in_2', 'Inline 2', value=None, offset=2, size=2),
                    t.input_text('field_in_3', 'Inline 3', value=None, offset=2, size=2),
                ),
                
                t.input_select('select_1', 'Select', value=1, options=[(0, 'Ok'), (1, 'Ok-ish'), (2, 'Not Ok')],
                               offset=2),
                t.input_textarea('textarea_1', 'Text Area 1', value="A text", offset=2, size=10),
            )
        ]


        jscode = ''

        return render_to_response("messy:templates/generic_page.mako", {
            'html': html,
            'code': jscode,
        }, request=self.request)

# EOF
