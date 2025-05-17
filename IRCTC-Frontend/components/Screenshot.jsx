import React from 'react';
import html2canvas from 'html2canvas';
import { saveAs } from 'file-saver';

const Screenshot = () => {
  const captureScreenshot = () => {
    const body = document.querySelector('body');
    html2canvas(body).then(canvas => {
      canvas.toBlob(blob => {
        saveAs(blob, 'screenshot.png');
      });
    });
  };

  return (
    <button onClick={captureScreenshot}>
      Take Screenshot
    </button>
  );
};

export default Screenshot;