INSERT INTO vendora_data.sales_transactions (
    LeadSource,
    LeadSourceCategory,
    DealNumber,
    SellingPrice,
    FrontGross,
    BackGross,
    TotalGross,
    SalesRepName,
    SplitSalesRep,
    VehicleYear,
    VehicleMake,
    VehicleModel,
    VehicleStockNumber,
    VehicleVIN
)
SELECT
    LeadSource,
    `LeadSource Category`,
    CAST(DealNumber AS STRING),
    CAST(REPLACE(REPLACE(CAST(SellingPrice AS STRING), '$', ''), ',', '') AS BIGNUMERIC),
    CAST(REPLACE(REPLACE(CAST(FrontGross AS STRING), '$', ''), ',', '') AS BIGNUMERIC),
    CAST(REPLACE(REPLACE(CAST(BackGross AS STRING), '$', ''), ',', '') AS BIGNUMERIC),
    CAST(REPLACE(REPLACE(CAST(`Total Gross` AS STRING), '$', ''), ',', '') AS BIGNUMERIC),
    SalesRepName,
    SplitSalesRep,
    VehicleYear,
    VehicleMake,
    VehicleModel,
    VehicleStockNumber,
    VehicleVIN
FROM
    vendora_data.sales_medium_staging;