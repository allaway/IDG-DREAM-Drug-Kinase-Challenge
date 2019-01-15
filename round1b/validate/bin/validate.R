require(rjson)
require(readr)
require(tidyr)
require(dplyr)
require(magrittr)
require(stringr)
library(argparse)

parser = ArgumentParser(description = "return status json")

parser$add_argument(
    "-s",
    "--submission_file",
    type = "character",
    required = TRUE,
    help = "submission file")

parser$add_argument(
    "-g",
    "--gold_standard",
    type = "character",
    required = TRUE,
    help = "gold_standard file")

args <- parser$parse_args()


REQUIRED_COLUMNS = list(
    "Compound_SMILES",
    "Compound_InchiKeys",
    "Compound_Name", 
    "UniProt_Id", 
    "Entrez_Gene_Symbol", 
    "DiscoveRx_Gene_Symbol", 
    "pKd_[M]_pred")  

get_submission_status_json <- function(submission_file, validation_file){
    status <- check_submission_file(submission_file, validation_file)
    if(status$status == "VALIDATED"){
        result_list = list(
            'prediction_file_errors' = "",
            'prediction_file_status' = status$status)
    } else {
        result_list = list(
            'prediction_file_errors' = stringr::str_c(
                status$reasons, 
                collapse = "\n"),
            'prediction_file_status' = status$status)
    }
    return(rjson::toJSON(result_list))
}

check_submission_file <- function(submission_file, validation_file){
    validation_df <- readr::read_csv(validation_file)
    
    status <- list("status" = "VALIDATED", "reasons" = c())
    
    status <- check_submission_file_readable(status, submission_file)
    
    if(status$status == "INVALID") return(status)
    
    submission_df <- readr::read_csv(submission_file)
    
    status <- check_submission_structure(status, validation_df, submission_df)
    
    if(status$status == "INVALID") return(status)
    
    status <- check_submission_values(status, submission_df)
    
    return(status)  
}


check_submission_file_readable <- function(status, submission_file){
    result <- try(readr::read_csv(submission_file), silent = TRUE)
    if (is.data.frame(result)){
        return(status)  
    } else {
        status$status = "INVALID"
        status$reasons = result[[1]]
        return(status)
    }
}


check_submission_structure <- function(status, validation_df, submission_df){
    
    if("pKd_[M]" %in% colnames(submission_df)) {
        status$status = "INVALID"
        status$reasons = "Submission file cannot have column: pKd_[M]" 
        return(status)
    }
    
    extra_columns <- submission_df %>% 
        colnames() %>% 
        setdiff(REQUIRED_COLUMNS) %>% 
        unlist()
    
    missing_columns <- REQUIRED_COLUMNS %>% 
        setdiff(colnames(submission_df)) %>% 
        unlist()
    
    extra_rows <- 
        left_join(submission_df, validation_df) %>% 
        mutate(n_row = 1:nrow(.)) %>% 
        filter(is.na(`pKd_[M]`)) %>% 
        use_series(n_row)
    
    missing_rows <- 
        left_join(validation_df, submission_df) %>% 
        mutate(n_row = 1:nrow(.)) %>% 
        filter(is.na(`pKd_[M]_pred`)) %>% 
        use_series(n_row)
    
    
    invalid_item_list <- list(
        extra_columns,
        missing_columns,
        extra_rows,
        missing_rows
    )
    
    error_messages <- c(
        "Submission file has extra columns: ",
        "Submission file has missing columns: ",
        "Submission file has missing rows: ",
        "Submission file has extra rows: "
    )
    
    for(i in 1:length(error_messages)){
        status <- update_submission_status_and_reasons(
            status,
            invalid_item_list[[i]],
            error_messages[[i]])
    }
    return(status)
}

check_submission_values <- function(status, submission_df){
    prediction_df <- submission_df %>% 
        dplyr::mutate(prediction = as.numeric(`pKd_[M]_pred`))
    contains_na <- prediction_df %>% 
        magrittr::use_series(prediction) %>% 
        is.na() %>% 
        any
    contains_inf <- prediction_df %>% 
        magrittr::use_series(prediction) %>% 
        is.infinite() %>% 
        any
    variance <- prediction_df %>% 
        magrittr::use_series(prediction) %>% 
        var() 
    if(contains_na) {
        status$status = "INVALID"
        status$reasons = "Submission_df missing numeric values" 
    }
    if(contains_inf) {
        status$status = "INVALID"
        status$reasons = c(status$reasons, "Submission_df missing numeric values")
    }
    if(variance == 0){
        status$status = "INVALID"
        status$reasons = c(status$reasons, "Submission_df predictions have a variance of 0")
    }
    return(status)
}





get_samples_from_df <- function(df){
    df %>% 
        dplyr::select(-cell_type) %>%
        colnames()
}

get_non_unique_items <- function(df){
    df %>% 
        dplyr::group_by(item_col) %>% 
        dplyr::summarise(count = dplyr::n()) %>% 
        dplyr::filter(count > 1) %>% 
        magrittr::use_series(item_col)
}

update_submission_status_and_reasons <- function(
    current_status, invalid_items, error_message){
    
    if (length(invalid_items) > 0){
        updated_status <- "INVALID"
        updated_reasons <- invalid_items %>%
            stringr::str_c(collapse = ", ") %>%
            stringr::str_c(error_message, .) %>%
            c(current_status$reasons, .)
    } else {
        updated_status <- current_status$status
        updated_reasons <- current_status$reasons
    }
    list("status" = updated_status, "reasons" = updated_reasons)
}

json <- get_submission_status_json(args$submission_file, args$gold_standard)
write(json, "results.json")
