export async function _info() {
    const rows = [];
    const response = await fetch('http://localhost:5000/getinfo');
    const data = await response.json();
    console.log(data);

    const info = data['info'];
    for (const i in info) {
        console.log(info[i]);
        const row = {
            id: i,
            buid: info[i]['buid'],
            name: info[i]['name'],
            email: info[i]['email'],
            github: info[i]['github'],
            semester: info[i]['semester'],
            project: info[i]['project_name'],
            repo: info[i]['repo'],
        };
        rows.push(row);
    }
    return rows;
}

export async function _csv() {
    const rows = [];
    const response = await fetch('http://localhost:5000/getcsv');
    const data = await response.json();
    console.log(data);

    const info = data['csv'];
    
    for (const i in info) {
        console.log(info[i]);
        const row = {
            id: i,
            semester: info[i]['semester'],
            course: info[i]['course'],
            project: info[i]['project'],
            organization: info[i]['organization'],
            team: info[i]['team'],
            role: info[i]['role'],
            fname: info[i]['fname'],
            lname: info[i]['lname'],
            name: info[i]['name'],
            email: info[i]['email'],
            buid: info[i]['buid'],
            github: info[i]['github'],
            process_status: info[i]['process_status'],
        };
        rows.push(row);
    }
    return rows;
}