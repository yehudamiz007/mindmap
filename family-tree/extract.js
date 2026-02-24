const fs = require('fs');
const b = fs.readFileSync('C:\\Users\\YEHUDA\\.openclaw\\media\\inbound\\img001---f3f36511-706c-4378-bfb9-5946a80675dc.pdf');
const jpegStart = b.indexOf(Buffer.from([0xff, 0xd8, 0xff]));
const jpegEnd = b.lastIndexOf(Buffer.from([0xff, 0xd9]));
console.log('JPEG start:', jpegStart, 'end:', jpegEnd);
if (jpegStart >= 0 && jpegEnd >= 0) {
    fs.writeFileSync('C:\\Users\\YEHUDA\\.openclaw\\workspace\\family-tree\\mizrachi-roots.jpg', b.slice(jpegStart, jpegEnd + 2));
    console.log('Extracted JPEG:', jpegEnd - jpegStart + 2, 'bytes');
} else {
    console.log('No JPEG found');
}
