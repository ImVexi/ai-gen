const utils = require("./utils")

var uuid = utils.generateUUID()
console.log(utils.checkUUID(uuid.split("-")[0]))