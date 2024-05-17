import { useDropzone } from 'react-dropzone';
import Box from '@mui/material/Box';
import { useEffect, useState } from 'react';
import { Button, Divider } from '@mui/material';
import General from './components/general/general';
import Csv from './components/csv/csv';
import Projects from './components/projects/projects';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Repos from './components/repos/repos';
import { API_URL } from './utils/uri';
import { useAuth } from './context/auth';
import { useFxns } from './context/fxns';
import { TabPanel, TabStyle } from './components/tab/tab';

function App() {

	const { _fetch, credentials } = useAuth();
	const { _csv, _csv_projects, _git_repos, _info, _projects } = useFxns();

	const [value, setValue] = useState(0);
	const [infoloading, setInfoLoading] = useState(false);
	const [csvloading, setCsvLoading] = useState(false);
	const [projectsloading, setProjectsLoading] = useState(false);
	const [reposloading, setReposLoading] = useState(false);
	const [inforows, setInfoRows] = useState<any[]>([]);
	const [csvrows, setCsvRows] = useState<any[]>([]);
	const [csvprojectsrows, setCsvProjectsRows] = useState<any[]>([]);
	const [projectsrows, setProjectsRows] = useState<any[]>([]);
	const [reposrows, setReposRows] = useState<any[]>([]);

	useEffect(() => { refresh();}, []);

	async function clearcache() {
		try {
			const response = await fetch(`${API_URL}/refresh`, { method: 'POST' });
			if (response.ok) {
				console.log('Cache cleared successfully');
				await refresh();
			}
		} catch (error) { console.error('Error clearing cache:', error); }
	}

	async function refresh() {
		console.log('Refreshing data');
		Promise.all([
			getfxn(_info, setInfoLoading, setInfoRows),
			getfxn(_csv, setCsvLoading, setCsvRows),
			getfxn(_csv_projects, setCsvLoading, setCsvProjectsRows),
			getfxn(_projects, setProjectsLoading, setProjectsRows),
			getfxn(_git_repos, setReposLoading, setReposRows),
		]);
	}


	async function getfxn(fxn: any, loadfxn: any, setfxn: any) {
		loadfxn(true);
		try { setfxn(await fxn()); }
		catch (error) { console.error('Error fetching data:', error); }
		finally { loadfxn(false); }
	}

	async function dropped(file: File, upload_url: string, ingest_url: string, setloading: any, setrows: any, fxn: any) {

		console.log(file);
		const formData = new FormData();
		formData.append("file", file);

		try {
			setloading(true);
			const response = await fetch(`${API_URL}/${upload_url}`, {
				headers: { 'Authorization': 'Basic ' + btoa(credentials.username + ":" + credentials.password) },
				method: 'POST',
				body: formData,
			});
			const result = await response.json();
			setloading(false);

			if (!response.ok) {
				console.error('Failed to upload file:', result);
				throw new Error(result.message);
			} else {getfxn(fxn, setloading, setrows);}

			console.log('File uploaded successfully:', result);

			setloading(true);
			const ingestreponse = await _fetch(`${API_URL}/${ingest_url}`, {method: 'POST'});
			const ingestresult = await ingestreponse.json();
			setloading(false);

			if (!ingestreponse.ok) {
				console.error('Failed to ingest file:', ingestresult);
				throw new Error(ingestresult.message);
			} else {clearcache();}

		} catch (error) {
			console.error('Error uploading file:', error);
		} finally {}

	}

	async function onCsvDrop(acceptedFiles: File[]) {
		const file = acceptedFiles[0];
		if (file) { dropped(file, 'upload/csv', 'ingest/csv', setCsvLoading, setCsvRows, _csv); }
	}
	async function onProjectsDrop(acceptedFiles: File[]) {
		const file = acceptedFiles[0];
		if (file) { dropped(file, 'upload/projects', 'ingest/projects', setCsvLoading, setCsvProjectsRows, _csv_projects); }
	}

	const { getRootProps: getCsvRootProps, getInputProps: getCsvInputProps, isDragActive: isCsvDragActive } = useDropzone({ onDrop: onCsvDrop });
	const { getRootProps: getProjectsRootProps, getInputProps: getProjectsInputProps, isDragActive: isProjectsDragActive } = useDropzone({ onDrop: onProjectsDrop });

	return (
		<>
			<h1>SPARK! AUTOMATIONS</h1>
			<Box sx={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
				<Tabs value={value} onChange={(event: React.SyntheticEvent, newValue: number) => { setValue(newValue); }} aria-label="basic tabs example">
					<Tab label="Actions" 		{...TabStyle(0)} />
					<Tab label="Github CRUD" 	{...TabStyle(1)} />
					<Tab label="Retool" 		{...TabStyle(2)} />
				</Tabs>

				<Button
					variant="outlined"
					color="primary"
					onClick={() => clearcache()}
				>
					refresh cache 🔄
				</Button>
			</Box>
			<Divider style={{ backgroundColor: '#fff', height: 3, marginTop: 20, marginBottom: 20 }} />

			<TabPanel value={value} index={0}>
				<h2>Current User Projects Repos Details</h2>
				<h4>General information about students & projects</h4>
				<General infoloading={infoloading} inforows={inforows} />

				<Divider style={{ backgroundColor: '#fff', height: 1, marginTop: 20, marginBottom: 20 }} />

				<h2>Ingest User Project Repos Details</h2>
				<h4>Upload CSV file for the CSV TABLE or the CSV_PROJECTS table</h4>
				<Box sx={{ display: 'flex', gap: 2, width: '100%'}}>
					<Box sx={{ flex: 1 }}>
						<div {...getCsvRootProps()} style={{ padding: 20, border: '2px dashed #007bff', borderRadius: 5, textAlign: 'center', cursor: 'pointer' }}>
							<input {...getCsvInputProps()} />
							{
								isCsvDragActive ?
									<p>Drop the file here ...</p> :
									<p><b>(CSV TABLE)</b> Drag and drop a CSV file here, or click to select a file</p>
							}
						</div>
					</Box>
					<Box sx={{ flex: 1 }}>
						<div {...getProjectsRootProps()} style={{ padding: 20, border: '2px dashed #007bff', borderRadius: 5, textAlign: 'center', cursor: 'pointer' }}>
							<input {...getProjectsInputProps()} />
							{
								isProjectsDragActive ?
									<p>Drop the file here ...</p> :
									<p><b>(PROJECTS TABLE)</b> Drag and drop a CSV file here, or click to select a file</p>
							}
						</div>
					</Box>
				</Box>

				<Csv csvloading={csvloading} csvrows={csvrows} csvprojectsrows={csvprojectsrows} callback={refresh} />

				<Divider style={{ backgroundColor: '#fff', height: 1, marginTop: 20, marginBottom: 20 }} />

				<h2>Set selected projects to Push/Pull</h2>
				<h4>(projects table) Select the projects you want to change to view / write</h4>
				<Projects projectsloading={projectsloading} projectsrows={projectsrows} callback={refresh} />


			</TabPanel>
			<TabPanel value={value} index={1}>
				<>
					<h2>CRUD: ALL REPOS</h2>
					<Repos reposloading={reposloading} reposrows={reposrows} />
				</>
			</TabPanel>
			<TabPanel value={value} index={2}>
				<iframe src="https://testgithub.retool.com/apps/automation%20dashboard" width="100%" height="800px"></iframe>
			</TabPanel>
		</>
	)
}

export default App
