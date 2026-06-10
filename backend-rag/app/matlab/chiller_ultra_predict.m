function [labels, probabilities] = chiller_ultra_predict(modelPath, X)
%CHILLER_ULTRA_PREDICT Run the final MATLAB ultra model for backend inference.
%   modelPath: path to largeDataset_enhanced_model.mat.
%   X: numeric matrix [numSamples x numFeatures].
%
%   The saved ultra model contains enhancedModel and, when available,
%   ensemble. The final experiment used CNN feature extraction followed by
%   the ensemble classifier, so this wrapper keeps that inference path.

    persistent cachedModelPath cachedEnhancedModel cachedEnsemble

    modelPath = char(modelPath);
    if isempty(cachedModelPath) || ~strcmp(cachedModelPath, modelPath)
        loaded = load(modelPath, 'enhancedModel', 'ensemble');
        if ~isfield(loaded, 'enhancedModel')
            error('模型文件中缺少 enhancedModel 变量。');
        end
        cachedEnhancedModel = loaded.enhancedModel;
        if isfield(loaded, 'ensemble')
            cachedEnsemble = loaded.ensemble;
        else
            cachedEnsemble = [];
        end
        cachedModelPath = modelPath;
    end

    X = double(X);

    if ~isempty(cachedEnsemble)
        features = cachedEnhancedModel.extractFeatures(X);
        [labels, probabilities] = cachedEnsemble.predictProba(features);
    else
        [labels, probabilities] = cachedEnhancedModel.predictProba(X);
    end

    labels = double(labels);
    probabilities = double(probabilities);
end
