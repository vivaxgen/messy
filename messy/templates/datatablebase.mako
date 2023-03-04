<%inherit file="rhombus:templates/base.mako" />

<!-- messy:datatablebase.mako -->

% if html:
${ html }
% else:
${ content | n }
% endif

##
<%def name="stylelinks()">
  <link href="/assets/rb/datatables/datatables.min.css" rel="stylesheet" />
</%def>
##
##
<%def name="jslinks()">
  <script src="/assets/rb/datatables/datatables.min.js"></script>
  <script src="/assets/rb/js/behave.js"></script>
</%def>
##
##
<%def name="jscode()">
  ${code or '' | n}
</%def>
##
##
