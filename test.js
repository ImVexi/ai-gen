var ffmetadata = require("ffmetadata");

ffmetadata.write("test.png", {encoder: "test"}, (err, data)=>{
    console.log(err, data)
    ffmetadata.read("test.png",(err, data)=>{
        console.log(err, data)
        })
})