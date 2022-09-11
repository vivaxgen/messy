
from rhombus.views import boolean_checkbox
from messy.views.sample import SampleViewer

import rhombus.lib.tags as t


class PathogenSampleViewer(SampleViewer):

    form_fields = SampleViewer.form_fields | {
        'storage_id': ('messy-sample-pathogen-storage_id', ),
        'passive_case_detection': ('messy-sample-pathogen-passive-detection', boolean_checkbox),
        'imported_case': ('messy-sample-pathogen-imported', boolean_checkbox),
        'recurrent': ('messy-sample-pathogen-recurrent', boolean_checkbox),
        'nationality_status': ('messy-sample-pathogen-nationality', boolean_checkbox),
        'method_id': ('messy-sammple-pathogen-method_id', ),
        'pcr_method_id': ('messy-sample-pathogen-pcr_method_id', ),
        'pcr_id': ('messy-sample-pathogen-pcr_id', ),
        'microscopy_id': ('messy-sample-pathogen-microscopy_id', ),
    }

    def index_helper(self):
        return super().index_helper()

    def view_helper(self):
        return super().view_helper()

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.obj
        dbh = self.dbh
        ff = self.ffn

        eform, js = super().edit_form(obj, create, readonly, update_dict)
        el = eform.elements['messy-sample-compulsory-fieldset']

        el.add(
            t.inline_inputs(
                t.checkboxes('messy-sample-case-statuss', 'Case status', [
                    (ff('passive_case_detection'), 'Passive detection',
                        obj.passive_case_detection),
                    (ff('imported_case'), 'Imported',
                        obj.imported_case),
                    (ff('recurrent'), 'Recurrent',
                        obj.recurrent),
                    (ff('nationality_status'), 'National',
                        obj.recurrent),
                ], offset=2),
            ),
        )

        el = eform.elements['messy-sample-additional-fieldset']
        el.add(
            t.inline_inputs(
                t.input_select_ek(ff('storage_id'), 'Storage type',
                                  value=obj.storage_id or dbh.get_ekey('NA', '@BLOOD-STORAGE').id,
                                  offset=2, size=2, parent_ek=dbh.get_ekey('@BLOOD-STORAGE')),
                t.input_select_ek(ff('method_id'), 'Withdrawal method',
                                  value=obj.method_id or dbh.get_ekey('NA', '@BLOOD-WITHDRAWAL').id,
                                  offset=2, size=2, parent_ek=dbh.get_ekey('@BLOOD-WITHDRAWAL')),
                t.input_select_ek(ff('microscopy_id'), 'Species by microscopy',
                                  value=obj.microscopy_id or dbh.get_ekey('no-species', '@SPECIES').id,
                                  offset=2, size=2, parent_ek=dbh.get_ekey('@SPECIES')),
            ),
        )

        return eform, js

# EOF
