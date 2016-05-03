// fork getUserMedia for multiple browser versions, for the future
// when more browsers support MediaRecorder

navigator.getUserMedia = ( navigator.getUserMedia ||
                       navigator.webkitGetUserMedia ||
                       navigator.mozGetUserMedia ||
                       navigator.msGetUserMedia);

// set up basic variables for app
var socket;
var all_images;
$(document).ready(function() {
        socket = io.connect('http://' + document.domain + ':' + location.port+'/main');
        console.log("Document ready");
        socket.on('disconnect', function() {
          socket.disconnect();
            });

        socket.on('img_file', function(data){
          var img = data.img;

          // Get a random image from directory of images and display it
          console.log("Selected image: " + img);
          img_src = document.querySelector(".central-img");
          img_src.setAttribute("src", "/static/img/" + img);

            });
        socket.emit('get_img_dir', '', function() {
                //window.location.reload(true);
            });

        });

// Entire window is loaded
$(window).load(function(){
  //var record = document.querySelector('.record');
  //var img_src = document.querySelector(".central-img");
  //
  //console.log("img src: " + img_src.getAttribute("src"));
  //console.log("record: " + record);
  //img_src.setAttribute("src",
  //    "/static/img/honda.jpeg");
  //console.log("All images: " + all_images);
});


var record = document.querySelector('.record');
var stop = document.querySelector('.stop');
var sendResponse = document.querySelector('.send');
var soundClips = document.querySelector('.sound-clips');
var canvas = document.querySelector('.visualizer');

console.log("Some code is being run here...");

// Replace image
console.log("Replacing image...");

// Ping server for image directory information

// disable stop button while not recording
stop.disabled = true;
var data = null;


// visualiser setup - create web audio api context and canvas
var audioCtx = new (window.AudioContext || webkitAudioContext)();
var canvasCtx = canvas.getContext("2d");

//main block for doing the audio recording

if (navigator.getUserMedia) {
  console.log('getUserMedia supported.');

  var constraints = { audio: true };
  var chunks = [];

  var onSuccess = function(stream) {  
    var mediaRecorder = new MediaRecorder(stream);

    visualize(stream);

    record.onclick = function() {
      mediaRecorder.start();
      console.log(mediaRecorder.state);
      console.log("recorder started");
      record.style.background = "red";

      stop.disabled = false;
      record.disabled = true;
    }

    stop.onclick = function() {
      mediaRecorder.stop();
      console.log("recorder stopped");
      record.style.background = "";
      record.style.color = "";
      // mediaRecorder.requestData();

      stop.disabled = true;
      record.disabled = false;
    }

    sendResponse.onclick = function(){
        console.log("Sending response...");
        //sendResponse.disabled = true;
        // Make sure data is actually valid audio file 
        socket.emit('submit_task', data, function() {
                        window.location.reload(true);
                    });

    }

    mediaRecorder.onstop = function(e) {
      console.log("data available after MediaRecorder.stop() called.");

      // TODO: Come up with better scheme for labelling audio clip
      var clipContainer = document.createElement('article');
      var clipLabel = document.createElement('p');
      var audio = document.createElement('audio');
      var deleteButton = document.createElement('button');
      
      clipContainer.classList.add('clip');
      audio.setAttribute('controls', '');
      deleteButton.textContent = 'Delete';
      deleteButton.className = 'delete';



      clipContainer.appendChild(audio);
      clipContainer.appendChild(clipLabel);
      clipContainer.appendChild(deleteButton);
      soundClips.appendChild(clipContainer);

      audio.controls = true;
      var blob = new Blob(chunks, { 'type' : 'audio/wav' });

      // assign data to blob
      data = blob;
      chunks = [];
      var audioURL = window.URL.createObjectURL(blob);
      audio.src = audioURL;

      console.log("Current URL: " + window.location.href);

      // To create a download link for audio file
      // hf = document.createElement('a');
      // hf.href = audioURL;
      // hf.innerHTML = "responseAudio";
      // hf.download = "audioLink";
      // soundClips.appendChild(hf);

      deleteButton.onclick = function(e) {
        evtTgt = e.target;
        evtTgt.parentNode.parentNode.removeChild(evtTgt.parentNode);
      }

    }

    mediaRecorder.ondataavailable = function(e) {
      chunks.push(e.data);
    }
  }

  var onError = function(err) {
    console.log('The following error occured: ' + err);
  }

  navigator.getUserMedia(constraints, onSuccess, onError);
} else {
   console.log('getUserMedia not supported on your browser!');
}

function visualize(stream) {
  var source = audioCtx.createMediaStreamSource(stream);

  var analyser = audioCtx.createAnalyser();
  analyser.fftSize = 2048;
  var bufferLength = analyser.frequencyBinCount;
  var dataArray = new Uint8Array(bufferLength);

  source.connect(analyser);
  //analyser.connect(audioCtx.destination);
  
  WIDTH = canvas.width
  HEIGHT = canvas.height;

  draw()

  function draw() {

    requestAnimationFrame(draw);

    analyser.getByteTimeDomainData(dataArray);

    canvasCtx.fillStyle = 'rgb(200, 200, 200)';
    canvasCtx.fillRect(0, 0, WIDTH, HEIGHT);

    canvasCtx.lineWidth = 2;
    canvasCtx.strokeStyle = 'rgb(0, 0, 0)';

    canvasCtx.beginPath();

    var sliceWidth = WIDTH * 1.0 / bufferLength;
    var x = 0;


    for(var i = 0; i < bufferLength; i++) {
 
      var v = dataArray[i] / 128.0;
      var y = v * HEIGHT/2;

      if(i === 0) {
        canvasCtx.moveTo(x, y);
      } else {
        canvasCtx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    canvasCtx.lineTo(canvas.width, canvas.height/2);
    canvasCtx.stroke();

  }
}
