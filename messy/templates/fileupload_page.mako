<%inherit file="rhombus:templates/base.mako" />

% if html:
${ html }
% else:
${ content | n }
% endif

##
<%def name="stylelinks()">
  <link rel="stylesheet" href="/assets/rb/select2/css/select2.min.css" />
  <link rel="stylesheet" href="/assets/rb/css/select2-bootstrap-5-theme.min.css" />
  <link rel="stylesheet" href="/assets/jQuery-File-Upload/css/jquery.fileupload.css" />
</%def>
##
##
<%def name="jslinks()">
  <script src="/assets/rb/select2/js/select2.min.js"></script>
  <script src="/assets/jQuery-File-Upload/js/vendor/jquery.ui.widget.js"></script>
  <script src="/assets/jQuery-File-Upload/js/jquery.fileupload.js"></script>
</%def>
##
##
<%def name="jscode()">
  ${code or '' | n}
</%def>
##
##
