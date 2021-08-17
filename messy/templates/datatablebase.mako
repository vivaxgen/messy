<%inherit file="rhombus:templates/base.mako" />

% if html:
${ html }
% else:
${ content | n }
% endif

##
<%def name="stylelinks()">
        <link href="${request.static_url('rhombus:static/datatables/datatables.min.css')}" rel="stylesheet" />
</%def>
##
##
<%def name="jslinks()">
        <script src="${request.static_url('rhombus:static/datatables/datatables.min.js')}"></script>
</%def>
##
##
<%def name="jscode()">
  ${code or '' | n}
</%def>
##
##
