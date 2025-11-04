// This script will iterate through all of the photos in a ShootProof Gallery and add them to a zip file that will be downloaded at the end
// Run from developer console in browser
// This requires JSZip library - we'll load it dynamically
var script = document.createElement('script');
script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
document.head.appendChild(script);

script.onload = function() {
  var downloadedImages = new Set();
  var imageData = [];
  var zip = new JSZip();

  function fetchCurrentImage() {
    return new Promise((resolve) => {
      var images = document.querySelectorAll('img');
      var foundNew = false;
      
      images.forEach((img) => {
        var src = img.src || img.getAttribute('ng-src');
        
        if (!src) return;
        
        if (src.startsWith('//')) {
          src = 'https:' + src;
        }
        
        if (downloadedImages.has(src)) {
          console.log('Already queued:', src);
          return;
        }
        
        downloadedImages.add(src);
        var urlParts = src.split('/');
        var filename = urlParts[urlParts.length - 1];
        
        imageData.push({ url: src, filename: filename });
        console.log('Queued:', filename);
        foundNew = true;
      });
      
      resolve(foundNew);
    });
  }

  function clickNextButton() {
    var nextButton = document.querySelector('a.photo-navigation-link-next');
    
    if (nextButton && !nextButton.classList.contains('disabled')) {
      nextButton.click();
      return true;
    }
    
    return false;
  }

  async function collectAllImages() {
    var wasNewImage = await fetchCurrentImage();
    
    if (!wasNewImage) {
      console.log('All images collected! Now downloading...');
      await downloadAsZip();
      return;
    }
    
    if (clickNextButton()) {
      setTimeout(collectAllImages, 2000);
    } else {
      console.log('All images collected! Now downloading...');
      await downloadAsZip();
    }
  }

  async function downloadAsZip() {
    console.log(`Fetching ${imageData.length} images...`);
    
    for (var i = 0; i < imageData.length; i++) {
      var item = imageData[i];
      try {
        var response = await fetch(item.url);
        var blob = await response.blob();
        zip.file(item.filename, blob);
        console.log(`Added to zip: ${item.filename} (${i + 1}/${imageData.length})`);
      } catch (error) {
        console.error(`Failed to fetch ${item.filename}:`, error);
      }
    }
    
    console.log('Creating zip file...');
    var zipBlob = await zip.generateAsync({ type: 'blob' });
    
    var a = document.createElement('a');
    a.href = URL.createObjectURL(zipBlob);
    a.download = 'gallery-images.zip';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    console.log('Download complete!');
  }

  console.log('Starting bulk download to ZIP...');
  collectAllImages();
};
