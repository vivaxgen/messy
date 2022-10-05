<%inherit file="rhombus:templates/base.mako" />

% if html:
${ html }
% else:
${ content | n }
% endif


<div class='col-md-8'>
<form enctype="multipart/form-data">
<input type="hidden" name='hid1' id='hid1' value="abc" />
<input type="file" id="upload-button" />
</form>
</div>

##
<%def name="stylelinks()">
  <link rel="stylesheet" href="/assets/rb/select2/css/select2.min.css" />
  <link rel="stylesheet" href="/assets/rb/css/select2-bootstrap-5-theme.min.css" />
  <!-- <link rel="stylesheet" href="/assets/jQuery-File-Upload/css/jquery.fileupload.css" /> -->
  <link rel="stylesheet" href="https://unpkg.com/dropzone@5/dist/min/dropzone.min.css" type="text/css" />
  <link rel="stylesheet" href="/assets/filepond/filepond.min.css" />

</%def>
##
##
<%def name="jslinks()">
  <script src="/assets/rb/select2/js/select2.min.js"></script>
  <script src="/assets/jQuery-File-Upload/js/vendor/jquery.ui.widget.js"></script>
  <script src="/assets/jQuery-File-Upload/js/jquery.fileupload.js"></script>
  <!-- <script src="https://unpkg.com/dropzone@5/dist/min/dropzone.min.js"></script> -->
  <script src="/assets/filepond/filepond.min.js"></script>
  <script src="/assets/filepond/filepond.jquery.js"></script>
</%def>
##
##
<%def name='jscode()'>

  let update_status = () => {
    $.get("${status_url | n}", (data) => {
      $('#status-view').html(data);
    });    
  };

  update_status();

  $('#upload-button').filepond(
  {
    server: {
      url: "${target_url | n}",
      fetch: null,
    },
    allowDrop: false,
    allowMultiple: true,
    ChunkUploads: true,
    chunkForce: true,
    chunkSize: 1048576, // 1MB = 1024 * 1024 bytes
    labelIdle: "Click to browse and select Fastq files",
    labelFileProcessingError: (error) => {
        headers = error.headers.split("\r\n");
        let header_map = {};
        headers.forEach((obj) => {
          tokens = obj.split(':');
          header_map[tokens[0]] = tokens[1]
          });
        return header_map['error-message'];
    },
    onprocessfile: (error) => {
      if (error) {
        // do nothing
      } else {
        update_status();
      };
    },
  });

</%def>

<%def name="jscode2()">

  const upload_url = '/uploadmgr/fastqpair/00000001VxvSN1zl6O4B7VCIXXXXXXXX@@target'

  const dropzone = new Dropzone("div#upload-button",
    {
      url: "/file/post" ,
      maxFilesize: 128,
      accept: function(file, done) {
        if (file.name != 'abc.def') {
          done("Naha, you don't.");
        }
        else { done(); }
      }
    }
  );

  ${code or '' | n}



</%def>
##
##
