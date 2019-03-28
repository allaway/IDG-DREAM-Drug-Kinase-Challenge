library(readr)
set.seed(98121)

template <- read_csv("../input/input.csv")

##example of random predictor algorithm
prediction <- rnorm(nrow(template), sd=1.5)+7
prediction[prediction<0] <- 0

##add prediction row to template
template$`pKd_[M]_pred` <- prediction

write_csv(template, "../output/prediction.csv")