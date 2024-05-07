// Store annotation rectangles and texts
var annotations = [];
var canvas, context;
var isDrawing = false,
  isDragging = false,
  isPanning = false;

var startX, startY, lastX, lastY;
var img; // This will hold the loaded image
var scale = 1,
  originX = 0,
  originY = 0; // Zoom and pan parameters

document.addEventListener("DOMContentLoaded", function () {
  canvas = document.getElementById("canvas");
  context = canvas.getContext("2d");
  canvas.addEventListener("mousedown", mouseDownHandler);
  canvas.addEventListener("mousemove", mouseMoveHandler);
  canvas.addEventListener("mouseup", mouseUpHandler);
  canvas.addEventListener("wheel", zoomImage, { passive: false });
  document.addEventListener("keydown", handleUndo);
  loadImage();
});

function mouseDownHandler(e) {
  var rect = canvas.getBoundingClientRect(); // Get the bounding rectangle of the canvas
  var scaleX = canvas.width / rect.width; // Relationship bitmap vs. element for X
  var scaleY = canvas.height / rect.height; // Relationship bitmap vs. element for Y

  if (e.button === 1) {
    // Middle mouse button
    isPanning = true;
    lastX = (e.clientX - rect.left) * scaleX;
    lastY = (e.clientY - rect.top) * scaleY;
    canvas.style.cursor = "move";
  } else if (!e.ctrlKey && e.button === 0) {
    // Ensure drawing starts with left mouse button without Ctrl
    isDrawing = true;
    startX = ((e.clientX - rect.left) * scaleX - originX) / scale;
    startY = ((e.clientY - rect.top) * scaleY - originY) / scale;
  }
}

// function mouseMoveHandler(e) {
//   if (isPanning) {
//     var dx = e.clientX - canvas.offsetLeft - lastX;
//     var dy = e.clientY - canvas.offsetTop - lastY;
//     originX += dx;
//     originY += dy;
//     lastX = e.clientX - canvas.offsetLeft;
//     lastY = e.clientY - canvas.offsetTop;
//     updateCanvas();
//   } else if (isDrawing) {
//     drawRectangle(e);
//   }
// }

function mouseMoveHandler(e) {
  if (isPanning) {
    var rect = canvas.getBoundingClientRect();
    var scaleX = canvas.width / rect.width;
    var scaleY = canvas.height / rect.height;
    var currentX = (e.clientX - rect.left) * scaleX;
    var currentY = (e.clientY - rect.top) * scaleY;

    var dx = currentX - lastX;
    var dy = currentY - lastY;

    originX += dx;
    originY += dy;

    lastX = currentX;
    lastY = currentY;
    updateCanvas();
  } else if (isDrawing) {
    drawRectangle(e);
  }
}

function mouseUpHandler(e) {
  if (isPanning) {
    isPanning = false;
    canvas.style.cursor = "default";
  } else if (isDrawing) {
    finishDrawing(e);
  }
}

function loadImage() {
  img = new Image();
  img.onload = updateCanvas;
  img.src = "/static/media/upload.jpg";
}

function updateCanvas() {
  context.setTransform(1, 0, 0, 1, 0, 0); // Reset transformation matrix to the identity matrix
  context.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas
  context.translate(originX, originY); // Apply panning
  context.scale(scale, scale); // Apply zoom
  context.drawImage(img, 0, 0); // Redraw the image
  drawAnnotations(); // Call a function specifically for drawing annotations
}

function drawAnnotations() {
  annotations.forEach(function (annot) {
    context.beginPath();
    context.rect(annot.x1, annot.y1, annot.x2 - annot.x1, annot.y2 - annot.y1);
    context.strokeStyle = "blue";
    context.lineWidth = 2 / scale; // Adjust line width based on current scale
    context.stroke();
    context.closePath();
    context.fillStyle = "blue";
    context.fillText(annot.text, annot.x1, annot.y1 - 5 / scale);
  });
}

function updateAnnotationsList() {
  console.log("Updating annotations list with:", annotations); // Add a log message
  var annotationsList = document.getElementById("annotationsDisplay");
  if (!annotationsList) {
    console.error("The annotationsList element was not found!");
    return;
  }
  annotationsList.innerHTML = ""; // 목록을 초기화합니다.

  // 목록에 새로운 바운더리 정보를 추가합니다.
  annotations.forEach(function (annot, index) {
    var li = document.createElement("li");
    li.textContent = `Annotation ${index + 1}: [${Math.round(
      annot.x1
    )}, ${Math.round(annot.y1)}] to [${Math.round(annot.x2)}, ${Math.round(
      annot.y2
    )}] - ${annot.text}`;
    annotationsList.appendChild(li);
  });
}

// function redrawAnnotations() {
//   console.log("Redrawing annotations with:", annotations); // Add a log message
//   context.setTransform(1, 0, 0, 1, 0, 0); // Reset transform to default before clearing
//   context.clearRect(0, 0, canvas.width, canvas.height); // Clear the entire canvas
//   updateCanvas(); // Redraw the image and existing annotations

//   annotations.forEach(function (annot) {
//     context.beginPath();
//     context.rect(annot.x1, annot.y1, annot.x2 - annot.x1, annot.y2 - annot.y1);
//     context.strokeStyle = "blue";
//     context.lineWidth = 2 / scale; // Adjust line width based on current scale
//     context.stroke();
//     context.closePath();
//     context.fillStyle = "blue";
//     context.fillText(annot.text, annot.x1, annot.y1 - 5 / scale);
//   });

//   updateAnnotationsList(); // UI 목록을 업데이트합니다.
// }

function redrawAnnotations() {
  context.setTransform(1, 0, 0, 1, 0, 0); // Reset transform to default before clearing
  context.clearRect(0, 0, canvas.width, canvas.height); // Clear the entire canvas
  updateCanvas(); // Redraw the image and existing annotations
}

function startDrawing(e) {
  if (!e.ctrlKey && e.button === 0) {
    // Ensure left mouse button without Ctrl for drawing
    isDrawing = true;
    startX = (e.clientX - canvas.offsetLeft - originX) / scale;
    startY = (e.clientY - canvas.offsetTop - originY) / scale;
  }
}

// function drawRectangle(e) {
//   if (!isDrawing) return;
//   var currentX = Math.round((e.clientX - canvas.offsetLeft - originX) / scale);
//   var currentY = Math.round((e.clientY - canvas.offsetTop - originY) / scale);

//   context.setTransform(1, 0, 0, 1, 0, 0); // Reset the transformation matrix to default
//   context.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas
//   updateCanvas(); // Redraw the image and previous annotations

//   var rectWidth = Math.round(currentX - startX);
//   var rectHeight = Math.round(currentY - startY);

//   var minSize = 5; // Minimum size of the rectangle in pixels
//   rectWidth = Math.max(rectWidth, minSize); // Apply minimum size
//   rectHeight = Math.max(rectHeight, minSize); // Apply minimum size

//   context.beginPath();
//   context.rect(startX, startY, rectWidth, rectHeight);
//   context.strokeStyle = "red";
//   context.lineWidth = 2 / scale; // Adjust line width according to the zoom level
//   context.stroke();
//   context.closePath();
// }

function drawRectangle(e) {
  if (!isDrawing) return;
  var rect = canvas.getBoundingClientRect();
  var scaleX = canvas.width / rect.width;
  var scaleY = canvas.height / rect.height;
  var coords = toOriginalCoords(
    (e.clientX - rect.left) * scaleX,
    (e.clientY - rect.top) * scaleY
  );
  var currentX = Math.round(coords.originalX);
  var currentY = Math.round(coords.originalY);

  context.setTransform(1, 0, 0, 1, 0, 0); // Reset the transformation matrix to default
  context.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas
  updateCanvas(); // Redraw the image and previous annotations

  var rectWidth = Math.round(currentX - startX);
  var rectHeight = Math.round(currentY - startY);

  context.beginPath();
  context.rect(startX, startY, rectWidth, rectHeight);
  context.strokeStyle = "red";
  context.lineWidth = 2 / scale; // Adjust line width according to the zoom level
  context.stroke();
  context.closePath();
}

// function finishDrawing(e) {
//   if (!isDrawing) return;
//   isDrawing = false;

//   // 마우스 좌표를 원본 이미지 기준 좌표로 변환
//   const { originalX: endX, originalY: endY } = toOriginalCoords(
//     e.clientX - canvas.offsetLeft,
//     e.clientY - canvas.offsetTop
//   );
//   const { originalX: startXOriginal, originalY: startYOriginal } =
//     toOriginalCoords(startX, startY);

//   const text = prompt("Enter annotation for this rectangle:", "");
//   if (text) {
//     annotations.push({
//       x1: Math.round(Math.min(startXOriginal, endX)),
//       y1: Math.round(Math.min(startYOriginal, endY)),
//       x2: Math.round(Math.max(startXOriginal, endX)),
//       y2: Math.round(Math.max(startYOriginal, endY)),
//       text: text,
//     });
//     console.log("Annotation added:", annotations[annotations.length - 1]);
//     redrawAnnotations();
//   }
// }

function finishDrawing(e) {
  if (!isDrawing) return;
  isDrawing = false;

  var rect = canvas.getBoundingClientRect();
  var scaleX = canvas.width / rect.width;
  var scaleY = canvas.height / rect.height;

  // 마우스 좌표를 원본 이미지 기준 좌표로 변환
  const coords = toOriginalCoords(
    (e.clientX - rect.left) * scaleX,
    (e.clientY - rect.top) * scaleY
  );
  const text = prompt("Enter annotation for this rectangle:", "");
  if (text) {
    annotations.push({
      x1: Math.round(Math.min(startX, coords.originalX)),
      y1: Math.round(Math.min(startY, coords.originalY)),
      x2: Math.round(Math.max(startX, coords.originalX)),
      y2: Math.round(Math.max(startY, coords.originalY)),
      text: text,
    });
    redrawAnnotations();
  }
}

function zoomImage(e) {
  e.preventDefault();
  var zoomIntensity = 0.1;
  var wheel = e.deltaY < 0 ? 1 : -1;
  var zoom = Math.exp(wheel * zoomIntensity);
  var oldScale = scale;
  scale *= zoom;
  originX -= (zoom - 1) * (e.clientX - canvas.offsetLeft - originX);
  originY -= (zoom - 1) * (e.clientY - canvas.offsetTop - originY);
  updateCanvas();
}

function undoLastAnnotation() {
  if (annotations.length > 0) {
    annotations.pop(); // Remove the last annotation
    updateCanvas();
  }
}

function handleUndo(e) {
  if (e.ctrlKey && e.key === "z") {
    undoLastAnnotation();
  }
}

function toOriginalCoords(x, y) {
  // 캔버스 좌표를 원본 이미지 좌표로 변환
  const originalX = (x - originX) / scale;
  const originalY = (y - originY) / scale;
  return { originalX, originalY };
}

function saveAnnotatedImage(annotationForm) {
  // 원본 이미지를 로드하고 주석을 반영
  const annotatedImg = new Image();
  annotatedImg.src = img.src; // 원본 이미지 경로
  annotatedImg.onload = function () {
    const offscreenCanvas = document.createElement("canvas");
    offscreenCanvas.width = annotatedImg.width;
    offscreenCanvas.height = annotatedImg.height;
    const offscreenContext = offscreenCanvas.getContext("2d");
    offscreenContext.drawImage(annotatedImg, 0, 0);

    // 주석을 원본 이미지에 추가
    annotations.forEach(function (annot) {
      offscreenContext.beginPath();
      offscreenContext.rect(
        annot.x1,
        annot.y1,
        annot.x2 - annot.x1,
        annot.y2 - annot.y1
      );
      offscreenContext.strokeStyle = "red";
      offscreenContext.lineWidth = 2; // 원본 크기에서 선 두께 조정
      offscreenContext.stroke();
      offscreenContext.closePath();
      offscreenContext.fillStyle = "red";
      offscreenContext.fillText(annot.text, annot.x1, annot.y1 - 5);
    });

    // 주석이 반영된 이미지를 Base64 데이터로 변환
    const dataURL = offscreenCanvas.toDataURL("image/jpeg");
    let imageInput = document.getElementById("annotatedImage");
    if (!imageInput) {
      imageInput = document.createElement("input");
      imageInput.setAttribute("type", "hidden");
      imageInput.setAttribute("name", "annotated_image");
      imageInput.setAttribute("id", "annotatedImage");
      annotationForm.appendChild(imageInput);
    }
    imageInput.value = dataURL;

    // 주석 이미지가 생성된 후에 폼을 제출합니다.
    annotationForm.submit();
  };
}

function toOriginalCoords(x, y) {
  // 캔버스 좌표를 원본 이미지 좌표로 변환
  const originalX = (x - originX) / scale;
  const originalY = (y - originY) / scale;
  return { originalX, originalY };
}

document.addEventListener("DOMContentLoaded", function () {
  const annotationForm = document.getElementById("annotationForm");
  const sendButton = document.getElementById("sendData");
  const undoButton = document.getElementById("undoLast"); // Get the undo button

  if (annotationForm && sendButton) {
    // Attach a click event listener to the sendButton
    sendButton.addEventListener("click", function (e) {
      e.preventDefault(); // Prevent the default form submission action
      saveAnnotatedImage(annotationForm);

      // Get the hidden input where annotations will be stored
      var annotationsInput = document.getElementById("annotationsInput");
      if (annotationsInput) {
        // Convert annotations array to JSON string and assign it to the input value
        annotationsInput.value = JSON.stringify(annotations);

        // Submit the form programmatically
        annotationForm.submit();
      }
    });
  }

  // Event listener for undo button
  if (undoButton) {
    undoButton.addEventListener("click", function (e) {
      e.preventDefault();
      undoLastAnnotation();
    });
  }
});
