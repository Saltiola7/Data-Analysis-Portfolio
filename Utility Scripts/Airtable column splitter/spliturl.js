let table = base.getTable('Blog Posts');
let field = 'Image - Assets';

let query = await table.selectRecordsAsync();

for (let record of query.records) {
    let urls = record.getCellValue(field);

    // split the URLs into an array
    let urlArray = urls.split(',');

    // trim whitespace from each URL
    for (let i = 0; i < urlArray.length; i++) {
        urlArray[i] = urlArray[i].trim();
    }

    // update the record with the individual URLs
    await table.updateRecordAsync(record, {
        'URL 1': urlArray[0],
        'URL 2': urlArray[1],
        'URL 3': urlArray[2],
        'URL 4': urlArray[3]
        // add more fields as needed
    });
}
