/**
 * a small retry wrapper with an incrameting 5s sleep delay
 * @param {*} fn 
 * @param {*} params 
 * @param {*} retries 
 * @param {*} maxRetries
 * @returns 
 */
async function retry(fn, params, retries = 0, maxRetries = 50) {
    try {
        const res = await  fn(...params);
        if(retries){
            console.log(`retry success after ${retries} retries`);
        } else {
            console.log('success on first try');
        }
        return res;
    } catch (e) {
        console.error(e);
        retries++;
        if(retries >= maxRetries){
            throw e;
        } 
        console.log(`retry #${retries}`);
        await new Promise(resolve => setTimeout(resolve, 1000 * 5 * retries));
        return retry(fn, params, retries);
    }
}
module.exports = { retry };