// k6 load test for the Quickfix API.
//
// Run against the API, never against https://riteshkr.online — that host is the
// Vercel-hosted static frontend. Vercel's Attack Challenge Mode starts serving
// 403s (`x-vercel-mitigated: challenge`) after a handful of requests from one IP
// and then drops connections outright, so any run pointed at it measures
// Vercel's DDoS shield rather than this application.
//
//   k6 run loadtest/api-smoke.js
//   k6 run -e BASE_URL=http://localhost:8000 loadtest/api-smoke.js

import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'https://customer-complaint-agent-new-1.onrender.com';

export const options = {
  // Ramping profile rather than a flat wall of VUs, so the point at which
  // latency degrades is visible in the results.
  stages: [
    { duration: '30s', target: 5 },
    { duration: '1m', target: 20 },
    { duration: '1m', target: 20 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    // A run that trips either of these is a real regression, not noise.
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<800'],
  },
};

// Render's free tier spins the service down when idle; the first request after
// that pays an ~80s cold start. Absorb it once here instead of letting it land
// on a VU and blow up the latency percentiles.
export function setup() {
  const res = http.get(`${BASE_URL}/health`, { timeout: '120s' });
  if (res.status !== 200) {
    throw new Error(`warm-up failed: ${BASE_URL}/health returned ${res.status}`);
  }
}

export default function () {
  const res = http.get(`${BASE_URL}/health`);

  check(res, {
    'status is 200': (r) => r.status === 200,
    // status 0 means the request never completed at the TCP/TLS layer. It is
    // worth asserting separately: a run full of status 0 at 0.00ms is the
    // signature of being blocked upstream, not of a slow application.
    'connection established': (r) => r.status !== 0,
  });

  // Think time. Without this each VU spins a tight loop — 100 VUs with no sleep
  // is what produced ~4000 req/s and tripped the upstream bot mitigation.
  sleep(1);
}
