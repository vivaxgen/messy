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
  <!-- plainbase.mako -->
  <head>
  <meta charset="utf-8" />
  <title>${request.get_resource('rhombus.title', None) or "Rhombus Framework"}</title>
  <meta name='viewport' content='width=device-width, initial-scale=1.0' />

  <!-- styles -->
  <link href="/assets/rb/bootstrap/css/bootstrap.min.css" rel="stylesheet" />
  <link href="/assets/rb/fontawesome/css/all.min.css" rel="stylesheet" />
  <link href="/assets/rb/fonts/source-sans-pro.css" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/css/custom.css')}" rel="stylesheet" />
  <link href="${request.static_url('messy:static/css/custom.css')}" rel="stylesheet" />

  ${self.stylelinks()}

  </head>
  <body>

  <nav class="navbar navbar-expand-md navbar-dark fixed-top bg-red p-0" id="fixedNavbar">
    <a class="navbar-brand px-3" href="/">${request.get_resource('rhombus.title', None) or "MESSy"}</a>
    <div class="collapse navbar-collapse px-3" id="navbarCollapse">
      <ul class="navbar-nav me-auto"></ul>
      <!-- user menu -->
      <div class="d-flex">
        ${user_menu(request)}
      </div>
    </div>
  </nav>

    <div class="container-fluid">
      <div class="row">

        <div class="col-md-12">
        ${next.body()}
        </div>

      </div>

    </div>

    <!-- footer -->
    <%include file="messy:templates/includes/footer.mako" />

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
    <script src="/assets/rb/js/jquery-3.6.0.min.js"></script>
    <script src="/assets/rb/bootstrap/js/bootstrap.bundle.min.js"></script>
</%def>
##
##
