import { Box } from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import React, { useState } from "react";

export default function General({ infoloading, inforows }: any) {

    const infocolumns: GridColDef[] = [
        { field: 'id', headerName: 'ID', flex: .25 },
        {
            field: 'project',
            headerName: 'project',
            editable: false,
            flex: 1.5,
        },
        {
            field: 'github_url',
            headerName: 'github url',
            editable: false,
            flex: 1.5,
        },
        {
            field: 'buid',
            headerName: 'buid',
            editable: false,
            flex: .75,
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
            field: 'github',
            headerName: 'github',
            editable: false,
            flex: 1,
        },
        {
            field: 'semester',
            headerName: 'semester',
            editable: false,
            flex: .75,
        },
        {
            field: 'status',
            headerName: 'status',
            editable: false,
            flex: 1,
        }

    ];
    return (
        <>
            <Box sx={{ height: 400, width: '100%', backgroundColor: "#242424" }}>
                <DataGrid
                    rows={inforows}
                    columns={infocolumns}
                    initialState={{
                        pagination: {
                            paginationModel: {
                                pageSize: 5,
                            },
                        },
                    }}
                    pageSizeOptions={[5]}   
                    disableRowSelectionOnClick
                    loading={infoloading}
                    style={
                        {
                            backgroundColor: '#fff',
                            color: 'black',
                        }
                    }
                />
            </Box>
        </>
    )
}