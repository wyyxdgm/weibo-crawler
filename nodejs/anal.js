var MongoClient = require("mongodb").MongoClient;
var url = "mongodb://localhost:27017/";
const tabletojson = require("tabletojson").Tabletojson;
// const exportFromJSON = require("export-from-json");
const { mongo_config } = require("../config.json");

if (mongo_config.port) {
  url = `mongodb://${mongo_config.host}:${mongo_config.port}`;
}
MongoClient.connect(url, function (err, db) {
  if (err) throw err;
  console.log("数据库链接成功!");
  var dbo = db.db("jobs");
  dbo
    .collection("jobs")
    .find({})
    .toArray(function (err, result) {
      // 返回集合中所有数据
      if (err) throw err;
      let alljobs = [];
      result = result.map((re) => {
        let str = re.res.replace(/jQuery\d+_\d+\((.*)\)/, "$1");
        let obj = JSON.parse(str);
        let tablehtml = obj.Rows[0];
        const converted = tabletojson.convert(tablehtml);
        console.log(converted);
        alljobs = alljobs.concat(converted);
        return tablehtml;
      });
      console.log("total:", alljobs.length);
      let resolvedJobs = [];
      const keys = {};
      alljobs.map((propsArr, index) => {
        let item = {};
        propsArr.map((ij, _idx) => {
          for (let idx = 0; idx < Object.keys(ij).length; idx++) {
            if (idx % 2 == 1) {
              let key = ij[idx - 1];
              item[key] = ij[idx];
              if (!keys[key]) keys[key] = 1;
            }
          }
        });
        console.log("done", index);
        resolvedJobs.push(item);
      });
      let keyArr = Object.keys(keys);
      console.log("keys", keyArr);
      resolvedJobs = resolvedJobs.map((obj) => keyArr.map((k) => obj[k] || ""));
      resolvedJobs.unshift(keyArr); // 插入表头
      // const fileName = "jobs";
      // const exportType = exportFromJSON.types.xls;

      // exportFromJSON({ data, fileName, exportType });
      const data = resolvedJobs;
      const path = require("path");
      var JE = require("json-xlsx");
      var je = new JE({ tmpDir: path.join(__dirname, "../tmp") });

      console.log(je.write(data)); // => /tmp/guid.xlsx

      db.close();
    });
});
