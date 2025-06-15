
export default {
  bootstrap: () => import('./main.server.mjs').then(m => m.default),
  inlineCriticalCss: true,
  baseHref: '/',
  locale: undefined,
  routes: [
  {
    "renderMode": 2,
    "route": "/"
  }
],
  entryPointToBrowserMapping: undefined,
  assets: {
    'index.csr.html': {size: 23964, hash: '619d71a0486dc9a15dac6b775a52e0aa7b8fbba9aa5796ae5490efa4d052ab71', text: () => import('./assets-chunks/index_csr_html.mjs').then(m => m.default)},
    'index.server.html': {size: 17302, hash: 'ca5a934af72d6db59da59e3fc934d44367369426a80c0c1e70334e5418414c25', text: () => import('./assets-chunks/index_server_html.mjs').then(m => m.default)},
    'index.html': {size: 30114, hash: 'edde344188322503c4e7796be3938719957ec080db20eea5b71e7a44f9fbbf38', text: () => import('./assets-chunks/index_html.mjs').then(m => m.default)},
    'styles-JPKTPMK7.css': {size: 7686, hash: 'wV6vDdsr1B8', text: () => import('./assets-chunks/styles-JPKTPMK7_css.mjs').then(m => m.default)}
  },
};
