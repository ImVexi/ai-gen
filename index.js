const dbBuilder = require("@airplanegobrr/database")
const express = require("express")
const bodyParser = require('body-parser')
const hbs = require('express-hbs');
const utils = require("./utils")
const fs = require("fs")
const path = require("path")
const app = express()
const eWS = require('express-ws')(app);
const db = new dbBuilder()

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

eWS.getWss().on("connection", (ws, msg)=>{
    ws.on("message", (data, bin)=>{
        console.log(data)
        ws.emit("message", "Hi!")
    })
})

app.use(bodyParser.json({limit: "100mb"})); // for parsing application/json
app.use(bodyParser.urlencoded({ extended: true })); // for parsing application/x-www-form-urlencoded

app.engine('hbs', hbs.express3())
app.set('view engine', 'hbs');
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
        
        for (var b64ImgIndex in req.body.images){
            var b64Img = req.body.images[b64ImgIndex]
            var imgb64 = Buffer.from(b64Img, "base64")
            var dir = `imgs/${data.username}`
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
            imgs: nextData.imgs ?? 1
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

app.use((req, res, next) => {
    var ip = (req.headers['x-forwarded-for'] || req.socket.remoteAddress).replace("::ffff:", "")
    console.log(`${ip} ${decodeURI(req.url)}`)
    req.rIP = ip
    next()
})

app.get("/", async (req, res) => {
    // res.sendFile(__dirname + "/index.html")
    res.render("index", {
        models: JSON.stringify(models),
        count: Object.keys(await db.get("inLine")).length
    })
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
        const files = fs.readdirSync(`imgs/${req.params.user}`)
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