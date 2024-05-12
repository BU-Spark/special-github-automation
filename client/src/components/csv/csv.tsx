import { DataGrid, GridColDef } from "@mui/x-data-grid";
import React from "react";

export default function Csv({ csvloading, csvrows }: any) {

    const csvcolumns: GridColDef[] = [
        { field: 'id', headerName: 'ID', width: 90 },
        {
            field: 'semester',
            headerName: 'semester',
            editable: false,
        },
        {
            field: 'course',
            headerName: 'course',
            editable: false,
        },
        {
            field: 'project',
            headerName: 'project',
            editable: false,
        },
        {
            field: 'organization',
            headerName: 'organization',
            editable: false,
        },
        {
            field: 'team',
            headerName: 'team',
            editable: false,
        },
        {
            field: 'role',
            headerName: 'role',
            editable: false,
        },
        {
            field: 'fname',
            headerName: 'fname',
            editable: false,
        },
        {
            field: 'lname',
            headerName: 'lname',
            editable: false,
        },
        {
            field: 'name',
            headerName: 'name',
            editable: false,
        },
        {
            field: 'email',
            headerName: 'email',
            editable: false,
        },
        {
            field: 'buid',
            headerName: 'buid',
            editable: false,
        },
        {
            field: 'github',
            headerName: 'github',
            editable: false,
        },
        {
            field: 'status',
            headerName: 'status',
            editable: false,
        },

    ];
    
    return (
        <>
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
        </>
    )
}