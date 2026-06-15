// The data-fetch signature every metric module exports.
//
// sdk is `any` because the SDK service constructors take `sdk as never`; the
// array return preserves the settled Promise<any[]> harness — SDK response
// interfaces lack implicit index signatures and are not assignable to
// Record<string, unknown>[], so any[] accepts SDK-typed arrays directly while
// still requiring an array return.
export type MetricFn = (sdk: any, getToken: () => Promise<string>) => Promise<any[]>
