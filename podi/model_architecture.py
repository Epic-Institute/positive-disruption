#!/usr/bin/env python

from diagrams import Cluster, Diagram
from diagrams.gcp.analytics import (
    BigQuery,
    Dataflow,
    Datalab,
    DataCatalog,
    Composer,
    Dataflow,
)
from diagrams.gcp.compute import AppEngine, Functions, GCE
from diagrams.gcp.database import BigTable, Datastore, Firestore, Memorystore
from diagrams.gcp.iot import IotCore
from diagrams.gcp.storage import GCS
from diagrams.onprem.client import Client, User
from diagrams.programming.language import Python
from diagrams.azure.web import MediaServices

with Diagram("PD Model Architecture", show=False):
    Usr = User("User-defined scenarios")

    with Cluster("Historical Data"):
        [GCS("Population, GDP"), GCS("Energy"), GCS("AFOLU")] - Usr

    with Cluster("Projection Parameters"):
        [IotCore("Energy"), IotCore("AFOLU")] - Usr

    with Cluster("Scneario Definition"):
        scen = [Dataflow("Baseline"), Dataflow("Pathway")]

    with Cluster("Compute Projections"):
        this = (
            scen
            >> Edge(color="grey")
            >> Functions("Energy Demand")
            >> Functions("Energy Supply")
            >> Edge(color="grey")
            >> BigTable("Energy Emissions")
        )
        Functions("AFOLU Demand") >> Functions("AFOLU Emissions")
        Functions("Additional Emissions")

    with Cluster("Results Analysis"):
        this >> Edge(color="grey") >> [
            DataCatalog("CDR Technology Mix"),
            DataCatalog("Co-benefits"),
            DataCatalog("Externalities"),
        ]

    with Cluster("Error Checking"):
        this >> Edge(color="grey") >> [
            DataCatalog("Results Reconciliation"),
            DataCatalog("Industrial Capacity"),
        ]

    Usr >> Edge(color="grey") >> scen
