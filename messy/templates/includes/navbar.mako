
<nav class="navbar navbar-expand-md navbar-dark fixed-top bg-red p-0" id="fixedNavbar">
  <a class="navbar-brand px-3" href="/">${request.get_resource('rhombus.title', None) or "MESSy"}</a>
  <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarCollapse" aria-controls="navbarCollapse" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
  </button>
  <div class="collapse navbar-collapse px-3" id="navbarCollapse">
    <ul class="navbar-nav mr-auto">
      <li class="nav-item active">
        <a class="nav-link" href="/sequence">Sequences</a>
      </li>
      <li class="nav-item active">
        <a class="nav-link" href="/sample">Samples</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="/collection">Collections</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="/run">Runs</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="/plate">Plates</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="/institution">Institutions</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="/upload">Upload</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="/tools">Tools</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="/help/index.rst">Help</a>
      </li>
    </ul>
    ${user_menu(request)}
  </div>
</nav>