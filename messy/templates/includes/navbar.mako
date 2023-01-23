
<nav class="navbar navbar-expand-md navbar-dark fixed-top bg-red p-0" id="fixedNavbar">
  <a class="navbar-brand px-3" href="/">${request.get_resource('rhombus.title', None) or "MESSy"}</a>
  <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarCollapse" aria-controls="navbarCollapse" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
  </button>
  <div class="collapse navbar-collapse px-3" id="navbarCollapse">
    ${main_menu()}
    <!-- user menu -->
    <div class="d-flex">
      ${user_menu(request)}
    </div>
  </div>
</nav>