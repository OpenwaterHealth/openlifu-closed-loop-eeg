// SPDX-License-Identifier: Apache-2.0

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const POSTER_FILES = [
  'poster/poster_template.html',
  'poster/lifu_poster.html',
];

const SECTION_IDS = ['why', 'pipeline', 'proof', 'limits'];

function navigationScript(html) {
  const start = html.indexOf('// ---- nav scroll-spy + smooth scroll ----');
  const end = html.indexOf('// ---- count-up stats ----', start);

  assert.notEqual(start, -1, 'navigation script is present');
  assert.notEqual(end, -1, 'navigation script has a closing boundary');
  return html.slice(start, end);
}

function runNavigationScript(html) {
  const sections = Object.fromEntries(
    SECTION_IDS.map((id) => [id, {
      id,
      scrollCalls: [],
      scrollIntoView(options) {
        this.scrollCalls.push(options);
      },
    }]),
  );
  const links = SECTION_IDS.map((id) => ({
    hash: `#${id}`,
    rewrittenHref: `//htmlpreview.github.io/?https://github.com/example/poster.html#${id}`,
    listeners: {},
    classList: { add() {}, remove() {} },
    getAttribute(name) {
      return name === 'href' ? this.rewrittenHref : null;
    },
    addEventListener(type, listener) {
      this.listeners[type] = listener;
    },
  }));
  const observed = [];

  class IntersectionObserver {
    constructor() {}
    observe(element) {
      observed.push(element.id);
    }
  }

  const document = {
    querySelectorAll(selector) {
      assert.equal(selector, '.nav-pill');
      return links;
    },
    getElementById(id) {
      return sections[id] ?? null;
    },
  };

  vm.runInNewContext(navigationScript(html), { document, IntersectionObserver });

  for (const [index, link] of links.entries()) {
    let prevented = false;
    link.listeners.click({ preventDefault() { prevented = true; } });
    assert.equal(prevented, true, `${SECTION_IDS[index]} prevents full-page navigation`);
  }

  return { observed, sections };
}

for (const posterFile of POSTER_FILES) {
  test(`${posterFile} resolves rewritten navigation links by URL fragment`, () => {
    const html = readFileSync(posterFile, 'utf8');
    const { observed, sections } = runNavigationScript(html);

    assert.deepEqual(observed, SECTION_IDS);
    for (const id of SECTION_IDS) {
      assert.equal(sections[id].scrollCalls.length, 1);
      assert.equal(sections[id].scrollCalls[0].behavior, 'smooth');
      assert.equal(sections[id].scrollCalls[0].block, 'start');
    }
  });
}
