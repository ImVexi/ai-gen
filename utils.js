const path = require('path');
const fs = require('fs');

const uuidMatch = {
    v1: /^[0-9A-F]{8}-[0-9A-F]{4}-[1][0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$/i,
    v2: /^[0-9A-F]{8}-[0-9A-F]{4}-[2][0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$/i,
    v3: /^[0-9A-F]{8}-[0-9A-F]{4}-[3][0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$/i,
    v4: /^[0-9A-F]{8}-[0-9A-F]{4}-[4][0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$/i,
    v5: /^[0-9A-F]{8}-[0-9A-F]{4}-[5][0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$/i
}

function checkUUID(uuid) {
    var uuidVersion = false
    for (var uuidVersionI in uuidMatch) {
        var uuidRegex = uuidMatch[uuidVersionI]
        if (uuidRegex.test(uuid)) {
            uuidVersion = uuidVersionI
            break
        }
    }
    return uuidVersion
}

function generateUUID() {
    let d = new Date().getTime();
    if (typeof performance !== 'undefined' && typeof performance.now === 'function') {
        d += performance.now();
    }
    const uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = (d + Math.random() * 16) % 16 | 0;
        d = Math.floor(d / 16);
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
    return uuid;
}

function getDirectorySize(path) {
    let totalSize = 0;

    const files = fs.readdirSync(path);

    files.forEach(function (file) {
        const fileOrDirPath = `${path}/${file}`;
        const stats = fs.statSync(fileOrDirPath);

        if (stats.isFile()) {
            totalSize += stats.size;
        } else if (stats.isDirectory()) {
            totalSize += getDirectorySize(fileOrDirPath);
        }
    });

    return totalSize;
}

function deleteFolderRecursive(folderPath) {
    if (fs.existsSync(folderPath)) {
      fs.readdirSync(folderPath).forEach(function(file, index){
        const curPath = path.join(folderPath, file);
        if (fs.lstatSync(curPath).isDirectory()) { // recurse
          deleteFolderRecursive(curPath);
        } else { // delete file
          fs.unlinkSync(curPath);
        }
      });
      fs.rmdirSync(folderPath);
    }
  }

module.exports = {
    generateUUID,
    checkUUID,
    getDirectorySize,
    deleteFolderRecursive
}