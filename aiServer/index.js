const dbBuilder = require("@airplanegobrr/database")
const express = require("express")
const basicAuth = require('express-basic-auth');
const bodyParser = require('body-parser')
const hbs = require('express-hbs');
const utils = require("../utils")
const fs = require("fs")
const path = require("path")
const app = express()
const eWS = require('express-ws')(app);
const db = new dbBuilder({filename:"aiServer/database.json"})
const logsDb = new dbBuilder({filename:"aiServer/logs.json", manual:true});
const axios = require("axios").default
const cacheAPIbase = axios.create({
    baseURL: "http://192.168.4.50:3505",
    headers: {
        "Content-Type": "application/json"
    }
})

const auth = basicAuth({
    users: { 'admin': 'secret123' },
    challenge: true,
    realm: 'My Application'
});

async function e(){
    await logsDb.load()
}
e()

let models = [
    "andite/anything-v4.0",
    "katakana/2D-Mix",
    "andite/pastel-mix",
    "runwayml/stable-diffusion-v1-5",
    "hakurei/waifu-diffusion",
    "johnslegers/epic-diffusion",
    "stabilityai/stable-diffusion-2-1",
    "22h/vintedois-diffusion-v0-1"
]

let uploading = false
let lastUserRequest = Infinity

eWS.getWss().on("connection", (ws, msg) => {
    ws.on("message", (data, bin) => {
        console.log(data)
        ws.emit("message", "Hi!")
    })
})

app.use(bodyParser.json({ limit: "100mb" })); // for parsing application/json
app.use(bodyParser.urlencoded({ extended: true })); // for parsing application/x-www-form-urlencoded

app.set('views', path.join(__dirname, '/views'));
app.engine('hbs', hbs.express3())
app.set('view engine', 'hbs');

app.use(async (req, res, next) => {
    var ip = (req.headers['x-forwarded-for'] || req.socket.remoteAddress).replace("::ffff:", "")
    var cleanURL = decodeURI(req.url)

    if (!cleanURL.includes("worker")) lastUserRequest = new Date().valueOf()

    var databaseIP = ip.replaceAll(".", "-")

    console.log(`${ip} ${cleanURL}`)
    req.rIP = ip
    var splitURL = cleanURL.replaceAll(".", "-").split("/")
    var maybeUUID = splitURL.pop()
    var isUUID = utils.checkUUID(maybeUUID)
    // if (isUUID) {
    //     var ipUUIDs = await logsDb.get(`${databaseIP}.jobIDs`)
    //     if (!ipUUIDs) {
    //         ipUUIDs = []
    //         logsDb.set(`${databaseIP}.jobIDs`, ipUUIDs)
    //     }
    //     if (!ipUUIDs.includes(maybeUUID)) {
    //         logsDb.push(`${databaseIP}.jobIDs`, maybeUUID)
    //     }
    // }
    splitURL.push(maybeUUID);
    var toSaveURL = splitURL.join("/")
    logsDb.add(`${databaseIP}.${toSaveURL}`, 1)
    if (uploading) {
        res.render("uploading")
    } else next()
})

setInterval(async () => {
    await logsDb.save()
    console.log("Saved logs")
}, 5*1000);

setInterval(async ()=>{
    if (uploading) return

    var jobCount = Object.keys(await db.get("inLine")).length
    if (jobCount >= 100){
        // console.log("Good1")
        if (lastUserRequest > new Date().valueOf()+5*60){
            // console.log("Good2")
            var inLine = await db.get("line")

            if (inLine && inLine.length != 0) return // Shouldn't happen
            // console.log("Good3")
            console.log("Clear to move data!")
            uploading = true // Stop requests
            var dataID = `${utils.generateUUID()}-${new Date().valueOf()}`
            const dbRes = await cacheAPIbase.post("/upload/database", {
                databaseID: dataID,
                database: {
                    inLine: await db.get("inLine"),
                    line: await db.get("line")
                }
            })
            if (dbRes.data && dbRes.data.good){
                // Ready to send the files!
                const folders = fs.readdirSync(`aiServer/imgs`)
                var uploaded = []
                for (var folder of folders){
                    const filesInFolder = fs.readdirSync(`aiServer/imgs/${folder}`)
                    // Send 10 images at a time
                    for (var i = 0; i < filesInFolder.length; i += 10) {
                        const images = filesInFolder.slice(i, i + 10)
                        //images has arrays with 10 images
                        const batch = {}
                        var e = []
                        for (var img of images){
                            // console.log(img, images)
                            
                            var imgData = fs.readFileSync(`aiServer/imgs/${folder}/${img}`)
                            batch[img] = imgData.toString("base64")
                            e.push(`${folder}/${img}`)
                        }
                        // console.log(batch)
                        // const sizeInBytes = (JSON.stringify(batch).length) / 1048576
                        // console.log(`Batch size: ${folder} ${sizeInMegabytes} MB`)
                        await cacheAPIbase.post("/upload/files", {
                            images: batch,
                            folder: folder,
                            databaseID: dataID
                        })
                        console.log(`Uploaded!`)
                        uploaded.push(...e)
                    }
                }

                console.log(uploaded)
                var check = []
                for (var str of uploaded){
                    var res = await cacheAPIbase.post(`/upload/check`, {
                        imgStr: str,
                        databaseID: dataID
                    })
                    check.push(res.data.found)
                }
                var allTrue = check.every(function(value) {
                    return value === true;
                });
                console.log(allTrue)
                uploading = false
                if (allTrue){
                    await db.set("inLine", {})
                    await db.set("line", [])
                    utils.deleteFolderRecursive("aiServer/imgs")
                    console.log("Cleared database!")
                }
            }
        }
    }
}, 60*1000)

const worker_api = express.Router()

worker_api.post("/add", async (req, res) => {
    res.json({
        good: true,
        workerID: 1
    })
})

worker_api.post("/upload", async (req, res) => {
    console.log(req.body)
    if (req.body && (req.body.image || req.body.images) && req.body.jobID) {
        var jobID = req.body.jobID
        var data = await db.get(`inLine.${jobID}`) ?? {}

        for (var b64ImgIndex in req.body.images) {
            var b64Img = req.body.images[b64ImgIndex]

            var imgb64 = Buffer.from(b64Img, "base64")
            

                // Do something with the base64 string, like send it as a response or save it to a file
                var dir = `aiServer/imgs/${data.username}`
                if (!fs.existsSync(dir)) {
                    fs.mkdirSync(dir, { recursive: true });
                }
                fs.writeFileSync(`${dir}/${jobID}-${b64ImgIndex}.png`, imgb64)
        }
        data.status = "FINISHED"
        await db.set(`inLine.${jobID}`, data)
    }
    res.send("ok.")
})

worker_api.get("/get", async (req, res) => {
    const line = await db.get(`line`)
    if (!line) return res.json({})
    const next = line.shift()
    if (next) {
        await db.set("line", line)
        const lineData = await db.get(`inLine`)
        const nextData = lineData[next]
        delete lineData[next].status
        // delete lineData[next]
        // console.log(next, nextData)
        res.json({
            jobID: next,
            prompt: nextData.prompt,
            model: nextData.model,
            sample: nextData.sample,
            good: true,
            imgs: nextData.imgs ?? 1,
            negPrompt: nextData.negPrompt ?? ""
        })
    } else {
        return res.json({})
    }
})

worker_api.post("/update", async (req, res) => {
    console.log(req.body)
    const jData = await db.get(`inLine.${req.body.jobID}`)
    await db.set(`inLine.${req.body.jobID}.prog`, (req.body.update) / jData.sample * 100)
    res.send("ok.")
})

worker_api.get("/types", async (req, res) => {
    res.json(models)
})

app.use("/worker", worker_api)

app.get("/", async (req, res) => {
    // res.sendFile(__dirname + "/index.html")
    res.render("index", {
        models: JSON.stringify(models),
        count: Object.keys(await db.get("inLine")).length
    })
})

app.use('/admin', auth, (req, res) => {
    // handle authenticated requests to /admin
    res.send("Hello admin!", req.auth)
});

app.get("/info", async (req, res) => {
    // res.sendFile(__dirname + "/index.html")
    res.render("info")
})

app.get("/queue/:id", async (req, res) => {
    //console.log(req.params.id)
    const lineData = await db.get(`inLine.${req.params.id}`)
    const line = await db.get("line")
    res.json({
        status: lineData?.status ?? "N/A",
        id: req.params.id,
        position: line?.indexOf(req.params.id) + 1,
        username: lineData?.username,
        progress: lineData?.prog ?? "N/A",
        count: lineData?.imgs ?? 0
    })
})

app.get("/generate", async (req, res) => {
    // console.log(req.query)
    var ID = utils.generateUUID()
    if (req.query.username == "" || req.query.username == null) req.query.username = "public"
    req.query.username ??= "public"
    var spl = req.query.sample.split("-")
    await db.set(`inLine.${ID}`, {
        prompt: req.query.prompt,
        negPrompt: req.query.negprompt ?? "",
        model: req.query.model,
        status: "wait",
        username: req.query.username ?? "public",
        sample: spl[0],
        imgs: spl[1] ?? 1
    })
    await db.push(`line`, ID)
    const line = await db.get("line")
    res.json({
        status: "QUEUED",
        id: ID,
        position: line.indexOf(ID) + 1,
        username: req.query.username
    })
})

app.get("/image/:id", async (req, res) => {
    if (!req.query.username) res.sendFile(path.join(__dirname, "imgs", "public", req.params.id + ".png")); else {
        res.sendFile(path.join(__dirname, "imgs", req.query.username, req.params.id + ".png"))
    }
})

app.get("/all/:user", async (req, res) => {
    try {
        const files = fs.readdirSync(`aiServer/imgs/${req.params.user}`)
        var html = `
    <style>
    .grid-container {
        display: grid;
        grid-template-columns: auto auto auto;
      }
    </style>
    <div class="grid-container">
    `

        for (var file of files) {
            var rawName = file.replace(".png", "")
            var allData = {}
            var noThinhg = rawName.split("-")
            noThinhg.pop()
            noThinhg = noThinhg.join("-")

            if (await db.has(`inLine.${noThinhg}`)) allData = await db.get(`inLine.${noThinhg}`)
            html += `<div style="border-style: solid; margin: 1;"><center><h1>${allData?.prompt ?? ""}</h1><h2>${allData?.model ?? ""} - ${allData?.sample ?? ""}</h2><img src="/image/${rawName}?username=${req.params.user}" style=""></center></div>`
        }

        html += "</div>"
        res.send(html)
    } catch (e) {
        res.send("error")
    }
})

app.listen(3504, () => {
    console.log("Running http://localhost:3504")
})

setInterval(async () => {
    var q = await db.get("line")
    if (!q) return
    console.log(`Quene is ${q.length} long!`)
}, 5000)