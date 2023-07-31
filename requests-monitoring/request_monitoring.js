const { default: Axios } = require("axios");
const fs = require("fs");
const moment = require("moment-timezone");


class Request {
  constructor({ url, method, data = {}, headers = {}, contentType = "application/json", }) {
    this.url = url;
    this.method = method;
    this.data = data;
    this.contentType = contentType;
    this.headers = headers;
  }

  async execute() {
    const startTime = moment();
    try {
      const response = await Axios.request({
        url: this.url,
        method: this.method,
        headers: this.headers,
        data: this.data,
      });

      const endTime = moment();
      const statusCode = response.status;
      const latency = moment(endTime).diff(startTime, 'milliseconds');
      const stats = { startTime, endTime, latency, statusCode };
      return { response, stats, error: null };

    } catch (error) {
      const endTime = moment();
      const statusCode = error.response.status;
      const latency = moment(endTime).diff(startTime, 'milliseconds');
      const stats = { startTime, endTime, latency, statusCode };
      return { response: null, stats, error };
    }
  }

  curl() {
    let headersString = this.contentType ? `--header 'content-type: ${this.contentType}'` : '';
    for (const key in this.headers) {
      headersString += ' --header ' + `'${key.toLowerCase()}: ${this.headers[key]}'` 
    }
    const curl = `curl --location --request ${this.method} ${this.url} '${this.data ? '--data ' + JSON.stringify(this.data) : "" }' ${headersString}`;
    return curl;
  }
}


export default class RequestMonitor {
	constructor({ timeFormat = "YYYY-MM-DD-HH:mm:ss-A", options = { logger: console } }) {
    this.timeFormat = timeFormat;
    this.logger = options.logger;
	}

  async request({ url, method, data, headers }) {
    const r = new Request({ url, method, data, headers });
    const { response, error, stats } = await r.execute();
    const curl = r.curl();
    this.log({ ...stats, ...r, curl });
    if (error) {
      throw error;
    }
    return response;
  }

  log({ url, method, latency, statusCode, startTime, curl }) {
    if (statusCode > 400) {
      this.logger.log(`\nCALLING: ${curl}`)
    }
    this.logger.log(
      `${startTime.format(this.timeFormat)} ${url} ${method} ${latency}ms ${statusCode}`
    )
  }

	
	getCurl({ url, method, data, contentType="application/json", headers }) {
    let headersString = `--header 'content-type: ${contentType}'`;
    for (const key in headers) {
      headersString += ' --header ' + `'${key.toLowerCase()}: ${headers[key]}'` 
    }
    const curl = `curl --location --request ${method} ${url} '${data ? '--data ' + JSON.stringify(data) : "" }' ${headersString}`;
    return curl;
  }
	
}

export class FileLogger {
  constructor({ filePath }) {
    this.filePath = filePath;
    if (!fs.existsSync(filePath)) {
        fs.writeFileSync(filePath, "");
    }
    this.stream = fs.createWriteStream(filePath, { flags: 'a', encoding: "utf-8", mode: "0666" });
  }
  
  log(logLine) {
    this.stream.write(logLine + '\n');
  }
}
