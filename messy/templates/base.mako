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
<%
  from rhombus.views.user import user_menu
%>
<html lang="en">
  <!-- base.mako -->
  <head>
  <meta charset="utf-8" />
  <title>${request.get_resource('rhombus.title', None) or "MESSy"}</title>
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

    <!-- Static navbar -->
    <%include file="messy:templates/includes/navbar.mako" />


    <div class="container-fluid">
      <div class="row"><div class='col'>
      ${flash_msg()}
      </div></div>
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

<!--

    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
      <script>window.jQuery || document.write('<script src="/docs/4.6/assets/js/vendor/jquery.slim.min.js"><\/script>')</script><script src="/assets/rb/bootstrap/js/bootstrap.bundle.min.js" integrity="sha384-Piv4xVNRyMGpqkS2by6br4gNJ7DXjqk09RmUpJ8jgGtD7zP9yug3goQfGII0yAns" crossorigin="anonymous"></script>
-->


    ${self.jslinks()}
    <script type="text/javascript">
        //<![CDATA[
        ${self.jscode()}
        //]]>
    </script>
</%def>
##
##
<%def name='flash_msg()'>
% if request.session.peek_flash():

  % for msg_type, msg_text in request.session.pop_flash():
   <div class="alert alert-${msg_type}">
     <a class="close" data-dismiss="alert">×</a>
     ${msg_text}
   </div>
  % endfor

% endif
</%def>

##
<%def name='jscode()'>
${ code or '' | n }
</%def>

##
<%def name="jslinks()">
${ codelink or '' | n }
</%def>
