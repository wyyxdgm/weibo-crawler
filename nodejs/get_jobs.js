const fetch = require("node-fetch");
fetch('http://www.baidu.com', {
        method: 'get',
        // headers: { 'Content-Type': 'application/json' },
    })
.then(res => res.text())
    .then(body => console.log(body));