function resultFilter(result, ignored) {
    result = result.filter(r => r?.value);

    const ignores = require('./ignore')[ignored];

    // Ignore dates
    result = result.filter(r => {
        if (!ignores?.length) return true;
        for (let ignore of ignores) {
            if (ignore[0] <= new Date(r.date).getTime() && ignore[1] >= new Date(r.date).getTime())
                return false
        }
        return true
    });

    // Sort results
    result = result.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    return result;
}

function ignoreDates(arr, ignored) {
    const ignores = require('./ignore')[ignored];

    for (let i = 0; i < arr.length; i++) {
        arr[i] = arr[i].filter(r => {
            if (!ignores?.length) return true;
            for (let ignore of ignores) {
                if (ignore[0] <= new Date(r.date).getTime() && ignore[1] >= new Date(r.date).getTime())
                    return false
            }
            return true
        });
    }

    return arr;
}

module.exports = { resultFilter, ignoreDates };