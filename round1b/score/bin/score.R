library(plyr)
library(doMC)
library(reticulate)
library(challengescoring)
library(argparse)
library(magrittr)
library(rjson)
library(tibble)
library(purrr)



parser = ArgumentParser(description = "Create directory with input files")

parser$add_argument(
    "-c",
    "--current_sub",
    type = "character",
    required = TRUE,
    help = "current submission file")

parser$add_argument(
    "-p",
    "--previous_sub",
    type = "character",
    help = "previous submission file")

parser$add_argument(
    "-g",
    "--gold_standard",
    type = "character",
    required = TRUE,
    help = "gold_standard file")

parser$add_argument(
    "-s",
    "--status",
    required = TRUE,
    type = "character",
    help = "current submission status")


args <- parser$parse_args()

if(args$status != "VALIDATED"){
    result_json <- 
        list("prediction_file_status" = args$status) %>% 
        rjson::toJSON()
    
} else {
    
    n_cores <- parallel::detectCores()
    
    if(is.na(n_cores) || n_cores <= 2){
        do_parallel <- F
    } else {
        do_parallel <- T
        doMC::registerDoMC(cores = n_cores -1)
    }
    
    reticulate::use_python("/usr/local/bin/python2")
    
    reticulate::source_python('/usr/local/bin/evaluation_metrics_python2.py')
    
    spearman_py <- function(gold, pred){
        gold_py <- gold %>% np_array()
        pred_py <- pred %>% np_array()
        spearman(gold_py, pred_py)
    }
    
    pearson_py <- function(gold, pred){
        gold_py <- gold %>% np_array()
        pred_py <- pred %>% np_array()
        pearson(gold_py, pred_py)
    }
    
    rmse_py <- function(gold, pred){
        gold_py <- gold %>% np_array()
        pred_py <- pred %>% np_array()
        rmse(gold_py, pred_py)
    }
    
    auc_py <- function(gold, pred){
        gold_py <- gold %>% as.data.frame() %>% r_to_py()
        pred_py <- pred %>% as.data.frame() %>% r_to_py()
        average_AUC(gold_py, pred_py)
    }
    
    ci_py <- function(gold, pred){
        gold_py <- gold %>% np_array()
        pred_py <- pred %>% np_array()
        ci(gold_py, pred_py)
    }
    
    f1_py <- function(gold, pred){
        gold_py <- gold %>% as.data.frame() %>% r_to_py()
        pred_py <- pred %>% as.data.frame() %>% r_to_py()
        f1(gold_py, pred_py)
    }
    
    param_df <- 
        tibble::tibble(
            # scoreFun = list(spearman_py, pearson_py, auc_py, ci_py, f1_py, rmse_py),
            scoreFun = list(spearman_py, pearson_py),
            # largerIsBetter = c(rep(T, 5), F),
            largerIsBetter = c(T, T),
            predictions = args$current_sub,
            predictionColname = 'pKd_.M._pred',
            goldStandard = args$gold_standard,
            goldStandardColname = 'pKd_.M.',
            doParallel = do_parallel
        ) 
    
    if (!is.null(args$previous_sub)){
        param_df$prevPredictions <- args$previous_sub
    }
    
    
    output <- param_df %>% 
        purrr::pmap(bootLadderBoot) %>% 
        # magrittr::set_names(c("spearman", "pearson", "auc", "ci", "f1", "rmse"))
        magrittr::set_names(c("spearman", "pearson"))
    
    output_scores <- purrr::map(output, "score")
    
    met_cutoff <- output %>% 
        magrittr::extract2("spearman") %>% 
        magrittr::extract2("metBayesCutoff")
    
    if(is.na(met_cutoff)) {
        met_cutoff <- T
    }
    
    result_json <- output_scores %>% 
        magrittr::inset("met_cutoff", value = met_cutoff) %>% 
        magrittr::inset("met_cutoff", value = met_cutoff) %>% 
        magrittr::inset("prediction_file_status", value = "SCORED") %>% 
        rjson::toJSON()
}

write(result_json, "results.json")


