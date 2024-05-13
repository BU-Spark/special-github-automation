import { Box, Button } from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import React from "react";

export default function Csv({ csvloading, csvrows }: any) {

    const csvcolumns: GridColDef[] = [
        { field: 'id', headerName: 'ID', flex: .25 },
        {
            field: 'semester',
            headerName: 'semester',
            editable: false,
            flex: 1,
        },
        {
            field: 'course',
            headerName: 'course',
            editable: false,
            flex: 1,
        },
        {
            field: 'project',
            headerName: 'project',
            editable: false,
            flex: 1,
        },
        {
            field: 'organization',
            headerName: 'organization',
            editable: false,
            flex: 1,
        },
        {
            field: 'team',
            headerName: 'team',
            editable: false,
            flex: 1,
        },
        {
            field: 'role',
            headerName: 'role',
            editable: false,
            flex: 1,
        },
        {
            field: 'fname',
            headerName: 'fname',
            editable: false,
            flex: 1,
        },
        {
            field: 'lname',
            headerName: 'lname',
            editable: false,
            flex: 1,
        },
        {
            field: 'name',
            headerName: 'name',
            editable: false,
            flex: 1,
        },
        {
            field: 'email',
            headerName: 'email',
            editable: false,
            flex: 1,
        },
        {
            field: 'buid',
            headerName: 'buid',
            editable: false,
            flex: 1,
        },
        {
            field: 'github',
            headerName: 'github',
            editable: false,
            flex: 1,
        },
        {
            field: 'status',
            headerName: 'status',
            editable: false,
            flex: 1,
        },

    ];

    return (
        <>
            <Box sx={{ height: 400, width: '100%', backgroundColor: "#242424", marginTop: 2, marginBottom: 2 }}>
                <DataGrid
                    rows={csvrows}
                    columns={csvcolumns}
                    initialState={{
                        pagination: {
                            paginationModel: {
                                pageSize: 5,
                            },
                        },
                    }}
                    pageSizeOptions={[5]}
                    disableRowSelectionOnClick
                    loading={csvloading}
                    style={
                        {
                            backgroundColor: '#fff',
                            color: 'black',
                        }
                    }
                />
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
                <Button variant='contained' color='primary'>
                    process ingested data into github (add students to repos)
                </Button>
            </Box>
        </>
    )
}