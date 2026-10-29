const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor() { this.children = []; this.style = {}; this.listeners = {}; this.textContent = ''; }
  set innerHTML(value) { throw Error('Dynamic HTML is forbidden in scan results'); }
  replaceChildren() { this.children = []; }
  insertRow() { const row = new Element(); row.cells = row.children; this.children.push(row); return row; }
  insertCell() { const cell = new Element(); this.children.push(cell); return cell; }
  appendChild(child) { this.children.push(child); }
  addEventListener(event, fn) { this.listeners[event] = fn; }
}
const bodies = { 'ipscan-results-body': new Element(), 'hostport-results-body': new Element() };
const context = { AppController: function () {}, document: {
  getElementById: id => bodies[id], createElement: () => new Element()
} };
vm.createContext(context);
vm.runInContext(fs.readFileSync('ITTools/web/js/network_tools.js', 'utf8'), context);
const app = new context.AppController();
const marker = '<img src=x onerror="throw 1">';
let copied;
app.copyToClipboard = value => { copied = value; };
app.renderIpScanResults([{ ip: '192.0.2.1', hostname: marker, vendor: marker, open_ports: [80, 3389] }]);
const row = bodies['ipscan-results-body'].children[0];
assert.equal(row.cells[3].textContent, marker);
row.cells[3].listeners.click();
assert.equal(copied, marker);
assert.equal(row.cells[7].children.length, 4);
app.renderHostPortScanResults([{ port: 80, name: marker, desc: marker, is_open: true }], '192.0.2.1');
assert.equal(bodies['hostport-results-body'].children[0].cells[1].textContent, marker);
app.renderIpScanResults([]);
assert.equal(bodies['ipscan-results-body'].children[0].cells[0].colSpan, 8);
console.log('PASS: network data stays text, clipboard/actions preserved, empty results handled.');
