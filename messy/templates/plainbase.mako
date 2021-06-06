## -*- coding: utf-8 -*-
% if request and request.is_xhr:
  ${next.body()}

  <script type="text/javascript">
    //<![CDATA[
    ${self.jscode()}
    //]]>
  </script>

% else:

<!DOCTYPE html>
<html lang="en">
  <head>
  <meta charset="utf-8" />
  <title>${request.get_resource('rhombus.title', None) or "Rhombus Framework"}</title>
  <meta name='viewport' content='width=device-width, initial-scale=1.0' />

  <!-- styles -->
  <link href="${request.static_url('rhombus:static/bootstrap/css/bootstrap.min.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/bootstrap/css/bootstrap-theme.min.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/fonts/source-sans-pro.css')}" rel="stylesheet" />

  ${self.stylelinks()}

  </head>
  <body>

    <div class="container-fluid">
      <div class="row">

        <div class="col-md-12">
        ${next.body()}
        </div>

      </div>

    </div>
    <footer>
    <div class="container-fluid">
      <div class='row'>
      <div class='col-md-12'>
        <!-- font: Nobile -->
        <p>Rhombus Framework Footer</p>
      </div>
      </div>
    </div>
    </footer>

${self.scriptlinks()}

  </body>

</html>
% endif
##
##
<%def name="stylelinks()">
</%def>
##
##
<%def name="scriptlinks()">
</%def>
##
##

