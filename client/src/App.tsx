import './App.css'
import { useDropzone } from 'react-dropzone';
import Box from '@mui/material/Box';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useEffect, useState } from 'react';
import { Button, Divider } from '@mui/material';
import { _csv, _info } from './fxns/fxns';
import General from './components/general/general';
import Csv from './components/csv/csv';

function App() {

	const [infoloading, setInfoLoading] = useState(false);
	const [csvloading, setCsvLoading] = useState(false);
	const [inforows, setInfoRows] = useState<any[]>([]);
	const [csvrows, setCsvRows] = useState<any[]>([]);
	useEffect(() => {
		getfxn(_info, setInfoLoading, setInfoRows);
		getfxn(_csv, setCsvLoading, setCsvRows);
	}, []);

	async function getfxn(fxn: any, loadfxn: any, setfxn: any) {
		loadfxn(true);
		try {
			const rows = await fxn();
			setfxn(rows);
		} catch (error) {
			console.error('Error fetching data:', error);
		} finally {
			loadfxn(false);
		}
	}

	async function onDrop(acceptedFiles: File[]) {
		setCsvLoading(true);
		const file = acceptedFiles[0];
		if (file) {
			console.log(file);
			const formData = new FormData();
			formData.append("file", file);

			try {
				const response = await fetch('http://localhost:5000/upload', {
					method: 'POST',
					body: formData,
				});
				const result = await response.json();
				if (response.ok) {
					console.log('File uploaded successfully:', result);
					await getfxn(_csv, setCsvLoading, setCsvRows);

					const ingestreponse = await fetch('http://localhost:5000/ingest', {
						method: 'POST',
					});
					const ingestresult = await ingestreponse.json();
					if (ingestreponse.ok) {
						console.log('Ingested successfully:', ingestresult);
						await getfxn(_info, setInfoLoading, setInfoRows);
					} else {
						console.error('Failed to ingest:', ingestresult);
						throw new Error(ingestresult.message);
					}
				} else {
					console.error('Failed to upload file:', result);
					throw new Error(result.message);
				}
			} catch (error) {
				console.error('Error uploading file:', error);
			}
		}
		setCsvLoading(false);
	};
	const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

	return (
		<>
			<h1>SPARK! AUTOMATIONS</h1>
			<Divider style={{ backgroundColor: '#007bff', height: 3, marginTop: 10, marginBottom: 10 }} />

			<h2>Current User Projects Repos Details</h2>
			<Box sx={{ height: 400, width: '100%', backgroundColor: "#242424"}}>
				<General infoloading={infoloading} inforows={inforows} />
			</Box>

			<h2>Ingest User Project Repos Details</h2>
			<div {...getRootProps()} style={{ padding: 20, border: '2px dashed #007bff', borderRadius: 5, textAlign: 'center', cursor: 'pointer' }}>
				<input {...getInputProps()} />
				{
					isDragActive ?
						<p>Drop the file here ...</p> :
						<p>Drag and drop a CSV file here, or click to select a file</p>
				}
			</div>
			<Box sx={{ height: 400, width: '100%', backgroundColor: "#242424", marginTop: 2}}>
				<Csv csvloading={csvloading} csvrows={csvrows} />
			</Box>

			<h2>fxn: set all projects to view only</h2>
			<Button variant="contained" color="primary" onClick={async () => {
				const response = await fetch('http://localhost:5000/purge', {
					method: 'POST',
				});
				const result = await response.json();
				if (response.ok) {
					console.log('Set all projects to view only:', result);
					await getfxn(_info, setInfoLoading, setInfoRows);
					await getfxn(_csv, setCsvLoading, setCsvRows);
				} else {
					console.error('Failed to set all projects to view only:', result);
					throw new Error(result.message);
				}
			}}
				style={{
					padding: 20,
				}}
			>Set All Projects to View Only</Button>
		</>
	)
}

export default App
