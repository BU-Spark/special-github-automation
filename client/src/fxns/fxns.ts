export async function _info() {
    const rows = [];
    const response = await fetch('http://localhost:5000/get_info');
    const data = await response.json();
    //console.log(data);

    const info = data['info'];
    for (const i in info) {
        //console.log(info[i]);
        const row = {
            id: i,
            buid: info[i]['buid'],
            name: info[i]['name'],
            email: info[i]['email'],
            github: info[i]['github'],
            semester: info[i]['semester'],
            project: info[i]['project_name'],
            github_url: info[i]['github_url'],
            status: info[i]['status'],
        };
        rows.push(row);
    }
    return rows;
}

export async function _csv() {
    const rows = [];
    const response = await fetch('http://localhost:5000/get_csv');
    const data = await response.json();
    //console.log(data);

    const info = data['csv'];
    
    for (const i in info) {
        //console.log(info[i]);
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
            status: info[i]['status'],
            project_github_url: info[i]['project_github_url'],
        };
        rows.push(row);
    }
    return rows;
}

export async function _projects() {
    console.log('getting projects');    
    const rows = [];
    const response = await fetch('http://localhost:5000/get_projects');
    const data = await response.json();
    console.log(data);

    const info = data['projects'];
    for (const i in info) {
        console.log(info[i]);
        const row = {
            id: i,
            name: info[i]['name'],
            semester: info[i]['semester'],
            github_url: info[i]['github_url'],
        };
        rows.push(row);
    }
    return rows;
}

export async function _git_repos() {
    const rows = [];
    const response = await fetch('http://localhost:5000/git/get_all_repos');
    const data = await response.json();
    console.log(data);

    const info = data['repos'];
    for (const i in info) {
        const row = {
            id: i,
            name: info[i][0],
            github_url: info[i][1]
        };
        rows.push(row);
    }
    return rows;
}