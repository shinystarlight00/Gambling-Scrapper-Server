/**
 * Returns the date to the exact upper hour
 * 
 * @param {Date} date 
 * @returns {Date}
 */
function roundToHour(date) {
    let p = 60 * 60 * 1000; // An hour
    return new Date(Math.ceil(date.getTime() / p ) * p);
}

module.exports = { roundToHour };