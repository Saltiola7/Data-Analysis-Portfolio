let table = base.getTable('Table Name'); // replace 'Table Name' with the name of your table
let field = 'Field Name'; // replace 'Field Name' with the name of the field containing the URLs

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
    // replace 'URL 1', 'URL 2', etc. with the names of your individual URL fields
    await table.updateRecordAsync(record, {
        'URL 1': urlArray[0],
        'URL 2': urlArray[1],
        'URL 3': urlArray[2],
        'URL 4': urlArray[3]
        // add more fields as needed
    });
}
