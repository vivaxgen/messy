
<nav class="navbar navbar-expand-md navbar-dark fixed-top bg-red p-0" id="fixedNavbar">
  <a class="navbar-brand px-3" href="/">${request.get_resource('rhombus.title', None) or "MESSy"}</a>
  <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarCollapse" aria-controls="navbarCollapse" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
  </button>
  <div class="collapse navbar-collapse px-3" id="navbarCollapse">
    <ul class="navbar-nav mr-auto">
      <li class="nav-item active dropdown">
        <a name="navbarDatamenu" id="navbarDatamenu" class="nav-link dropdown-toggle" data-bs-toggle="dropdown" role="button" aria-expanded="false">Data</a>
        <ul class="dropdown-menu" aria-labelledby="navbarDatamenu">
          <li><a class="dropdown-item" href="/collection">Collection</a></li>
          <li><a class="dropdown-item" href="/sample">Sample (panel)</a></li>
          <li><a class="dropdown-item" href="/sample">Sample (metadata)</a></li>
          <li><a class="dropdown-item" href="/institution">Institution</a></li>
          <hr>
          <li><a class="dropdown-item" href="/plate">Plates</a></li>
          <li><a class="dropdown-item" href="/run">Run</a></li>
        </ul>
      </li>
      <li class="nav-item active dropdown">
        <a name="navbarMarkermenu" id="navbarMarkermenu" class="nav-link dropdown-toggle" data-bs-toggle="dropdown" role="button" aria-expanded="false">Marker</a>
        <ul class="dropdown-menu" aria-labelledby="navbarMarkermenu">
          <li><a class="dropdown-item" href="/panel">Panel</a></li>
          <li><a class="dropdown-item" href="/variant">Variant</a></li>
        </ul>
      </li>
      <li class="nav-item active dropdown">
        <a name="navbarAnalysismenu" id="navbarMarkermenu" class="nav-link dropdown-toggle" data-bs-toggle="dropdown" role="button" aria-expanded="false">Analysis</a>
        <ul class="dropdown-menu" aria-labelledby="navbarAnalysismenu">
          <li><a class="dropdown-item" href="/analysis/allele">Allele Frequency</a></li>
          <li><a class="dropdown-item" href="/analysis/nj">Neighbor-Joining</a></li>
          <li><a class="dropdown-item" href="/analysis/pca">PCA</a></li>
          <li><a class="dropdown-item" href="/analysis/coi">COI</a></li>
        </ul>
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